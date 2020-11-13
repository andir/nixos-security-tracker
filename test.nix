{ pkgs ? import ./nix }:
let
  common = {
    imports = [ ./module.nix ];
    services.nixos-security-tracker.enable = true;

    # use one static file for the NVD dataset that is imported
    systemd.services.nixos-security-tracker-update.environment.NIXOS_SECURITY_TRACKER_NVD_URLS = "http://localhost/nvd-data.json.gz";
    systemd.services.nixos-security-tracker-update-recent.environment.NIXOS_SECURITY_TRACKER_NVD_URLS = "http://localhost/nvd-data.json.gz";

    services.nginx = {
      enable = true;
      virtualHosts.localhost.locations."=/nvd-data.json.gz" = {
        alias = "${./tracker/tests/fixtures/nvdcve-1.1-2002-stripped.json.gz}";
      };
    };
  };
in
pkgs.nixosTest {
  nodes = {
    sqlite = {
      imports = [ common ];
      services.nixos-security-tracker.database = "sqlite";
    };
    postgresql = { config, ... }: {
      imports = [ common ];
      services.nixos-security-tracker = {
        database = "postgresql";
      };
    };
  };
  testScript = ''
    # fmt: off
    def test_server(server):
      server.wait_for_unit("multi-user.target")
      server.wait_for_unit("nginx.service")
      server.wait_for_open_port(80)
      server.succeed("curl -s --fail localhost")
      server.succeed("curl -s --fail localhost/static/admin/js/core.js")

      with subtest("NVD import"):
          # at first there must be no errors and no CVE's
          server.succeed("curl -s --fail localhost/issues/")
          server.succeed("curl -s --fail localhost/issues/ | grep -qv CVE-")

          # run the update & wait until it finishes
          server.systemctl("start --wait nixos-security-tracker-update.service")

          # now there should not be any errors and we must also be able to find a CVE
          server.succeed("curl -s --fail localhost/issues/")
          server.succeed("curl -s --fail localhost/issues/ | grep -q CVE-")
      server.shutdown()

    test_server(sqlite)
    test_server(postgresql)
  '';
}
