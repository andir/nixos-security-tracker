{ pkgs, lib, config, ... }:
let
  cfg = config.services.nixos-security-tracker;
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
        envFile = pkgs.writeText "env" ''
          export NIXOS_SECURITY_TRACKER_DATABASE_NAME="$STATE_DIRECTORY/database.sqlite"
        '';
      in
      {
        nixos-security-tracker-migrate = lib.mkIf cfg.runMigrations {
          wantedBy = [ "multi-user.target" ];
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
            DynamicUser = true;
            RemainAfterExit = true;
            StateDirectory = "nixos-security-tracker";
            PrivateTemp = true;
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
            StateDirectory = "nixos-security-tracker";
            PrivateTemp = true;
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
            StateDirectory = "nixos-security-tracker";
            PrivateTemp = true;
          };
        };
      };
  };
}
