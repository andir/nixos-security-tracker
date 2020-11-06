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
        nixos-security-tracker = super.callPackage ./default.nix { };
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

    systemd.services.nixos-security-tracker =
      let
        envFile = pkgs.writeText "env" ''
          export NIXOS_SECURITY_TRACKER_DATABASE_NAME="$STATE_DIRECTORY/database.sqlite"
        '';
      in
      {
        path = [
          pkgs.nixos-security-tracker.manage
          pkgs.nixos-security-tracker.env
        ];
        environment = {
          ENVFILE = toString envFile;
        };
        preStart = lib.mkIf cfg.runMigrations '' source $ENVFILE
        exec manage migrate
      '';
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
}
