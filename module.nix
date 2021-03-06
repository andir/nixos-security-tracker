{ pkgs, lib, config, ... }:
let
  cfg = config.services.nixos-security-tracker;

  haveLocalPostgresql = cfg.database == "postgresql" && (cfg.postgresqlHost == "localhost" || cfg.postgresqlHost == "");
in
{
  options = {
    services.nixos-security-tracker = {
      enable = lib.mkEnableOption "NixOS Security Tracker";
      runMigrations = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = ''
          Whether migrations should be run on startup.
        '';
      };
      githubEventsSharedSecretFile = lib.mkOption {
        type = lib.types.nullOr lib.types.str;
        default = null;
      };
      database = lib.mkOption {
        type = lib.types.enum [ "sqlite" "postgresql" ];
        default = "sqlite";
      };
      postgresqlHost = lib.mkOption {
        type = lib.types.str;
        default = "";
      };
      postgresqlUser = lib.mkOption {
        type = lib.types.str;
        default = "nixos_security_tracker";
      };
      postgresqlPort = lib.mkOption {
        type = lib.types.str;
        default = "";
      };
      postgresqlSchemaName = lib.mkOption {
        type = lib.types.str;
        default = "nixos_security_tracker";
      };
      postgresqlPasswordFile = lib.mkOption {
        type = lib.types.nullOr lib.types.str;
        default = null;
      };
      scheduleNVDUpdates = lib.mkOption {
        type = lib.types.bool;
        default = true;
        description = ''
          Whether updates from the NVD CVE database should be imported regularly.
        '';
      };
      virtualHost = lib.mkOption {
        type = lib.types.str;
        default = "localhost";
        description = ''
          The NGINX virtualhost for this application.
        '';
      };
      workers = lib.mkOption {
        type = lib.types.int;
        default = 2;
        description = ''
          Numbe of worker processes>
        '';
      };
    };
  };
  config = lib.mkIf cfg.enable {
    nixpkgs.overlays = [
      (self: super: {
        nixos-security-tracker = import ./default.nix { };
      })
    ];

    services.postgresql = lib.mkIf haveLocalPostgresql {
      enable = true;
      identMap = ''
        nixos-security-tracker nixos-security-tracker ${cfg.postgresqlUser}
      '';
      authentication = ''
        local ${cfg.postgresqlSchemaName} all ident map=nixos-security-tracker
      '';
      ensureDatabases = [ cfg.postgresqlSchemaName ];
      ensureUsers = [
        {
          name = "${cfg.postgresqlUser}";
          ensurePermissions = {
            "DATABASE ${cfg.postgresqlSchemaName}" = "ALL PRIVILEGES";
          };
        }
      ];

    };

    services.nginx.virtualHosts.${cfg.virtualHost} = {
      locations."/".proxyPass = "http://unix:/run/nixos-security-tracker/gunicorn.sock";
      locations."/static/" = {
        alias = "${pkgs.nixos-security-tracker.staticFiles}/";
      };
    };

    systemd.sockets.nixos-security-tracker = {
      listenStreams = [
        "/run/nixos-security-tracker/gunicorn.sock"
      ];
      wantedBy = [ "sockets.target" ];
    };

    systemd.services =
      let
        envFile = pkgs.writeText "env" ((lib.optionalString (cfg.githubEventsSharedSecretFile != null) ''
          export NIXOS_SECURITY_TRACKER_GITHUB_EVENTS_SECRET="$(<${cfg.githubEventsSharedSecretFile})"
        '') + (if cfg.database == "sqlite" then ''
          export NIXOS_SECURITY_TRACKER_DATABASE_TYPE="sqlite"
          export NIXOS_SECURITY_TRACKER_DATABASE_NAME="$STATE_DIRECTORY/database.sqlite"
        '' else if cfg.database == "postgresql" then ''
          export NIXOS_SECURITY_TRACKER_DATABASE_TYPE="postgresql"
          export NIXOS_SECURITY_TRACKER_DATABASE_NAME="${cfg.postgresqlSchemaName}"
          export NIXOS_SECURITY_TRACKER_DATABASE_HOST="${cfg.postgresqlHost}"
          export NIXOS_SECURITY_TRACKER_DATABASE_USER="${cfg.postgresqlUser}"
          export NIXOS_SECURITY_TRACKER_DATABASE_PORT="${cfg.postgresqlPort}"
          ${lib.optionalString (cfg.postgresqlPasswordFile != null) ''
            export NIXOS_SECURITY_TRACKER_DATABASE_PASSWORD="$(<${cfg.postgresqlPasswordFile})"
          ''}
        '' else throw "unexpected database type ${cfg.database}") + ''
          SECRET_KEY_FILE="$STATE_DIRECTORY/secret-key"
          test -f "$SECRET_KEY_FILE" || tr -dc A-Za-z0-9 < /dev/urandom  | head -c 128 > "$SECRET_KEY_FILE"

          export NIXOS_SECURITY_TRACKER_SECRET_KEY="$(<$SECRET_KEY_FILE)"
        '');
      in
      {

        nixos-security-tracker-migrate = lib.mkIf cfg.runMigrations {
          wantedBy = [ "multi-user.target" ];
          after = lib.mkIf haveLocalPostgresql [
            "postgresql.service"
          ];
          requires = lib.mkIf haveLocalPostgresql [
            "postgresql.service"
          ];

          path = [
            pkgs.nixos-security-tracker.manage
          ];
          environment = {
            ENVFILE = toString envFile;
          };
          script = lib.mkIf cfg.runMigrations ''
            source $ENVFILE
            exec manage migrate
          '';
          serviceConfig = {
            Type = "oneshot";
            User = "nixos-security-tracker";
            DynamicUser = true;
            RemainAfterExit = true;
            StateDirectory = "nixos-security-tracker";
            PrivateTmp = true;
          };
        };

        nixos-security-tracker-update = lib.mkIf cfg.scheduleNVDUpdates {
          path = [
            pkgs.nixos-security-tracker.manage
            pkgs.nixos-security-tracker.env
          ];
          environment = {
            ENVFILE = toString envFile;
          };

          after = lib.mkIf cfg.runMigrations [ "nixos-security-tracker-migrate.service" ];
          requires = lib.mkIf cfg.runMigrations [ "nixos-security-tracker-migrate.service" ];

          script = ''
            source $ENVFILE
            exec manage import_nvd
          '';

          startAt = "daily"; # FIXME: make configurable

          serviceConfig = {
            Type = "oneshot";
            DynamicUser = true;
            User = "nixos-security-tracker";
            StateDirectory = "nixos-security-tracker";
            PrivateTmp = true;
          };
        };

        nixos-security-tracker-update-recent = lib.mkIf cfg.scheduleNVDUpdates {
          path = [
            pkgs.nixos-security-tracker.manage
            pkgs.nixos-security-tracker.env
          ];
          environment = {
            ENVFILE = toString envFile;
          };

          after = lib.mkIf cfg.runMigrations [ "nixos-security-tracker-migrate.service" ];
          requires = lib.mkIf cfg.runMigrations [ "nixos-security-tracker-migrate.service" ];

          script = ''
            source $ENVFILE
            exec manage import_nvd https://nvd.nist.gov/feeds/json/cve/1.1/nvdcve-1.1-recent.json.gz
          '';

          startAt = "hourly"; # FIXME: make configurable

          serviceConfig = {
            Type = "oneshot";
            User = "nixos-security-tracker";
            DynamicUser = true;
            StateDirectory = "nixos-security-tracker";
            PrivateTmp = true;
          };
        };

        nixos-security-tracker = {
          path = [
            pkgs.nixos-security-tracker.manage
            pkgs.nixos-security-tracker.env
          ];
          environment = {
            ENVFILE = toString envFile;
          };
          after = lib.mkIf cfg.runMigrations [ "nixos-security-tracker-migrate.service" ];
          requires = lib.mkIf cfg.runMigrations [ "nixos-security-tracker-migrate.service" ];
          script = ''
            source $ENVFILE
            exec gunicorn ${pkgs.nixos-security-tracker.asgiPath} \
              -k uvicorn.workers.UvicornWorker \
              --name nixos-security-tracker \
              --workers ${toString cfg.workers}
          '';
          serviceConfig = {
            ExecReload = "${pkgs.coreutils}/bin/kill -s HUP $MAINPID";
            Type = "notify";
            DynamicUser = true;
            User = "nixos-security-tracker";
            StateDirectory = "nixos-security-tracker";
            PrivateTmp = true;
          };
        };
      };
  };
}
