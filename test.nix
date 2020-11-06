{ pkgs ? import ./nix }:
pkgs.nixosTest {
  nodes = {
    server = {
      imports = [ ./module.nix ];
      services.nixos-security-tracker.enable = true;
      services.nginx.enable = true;
    };
  };
  testScript = ''
    server.wait_for_unit("multi-user.target")
    server.wait_for_unit("nginx.service")
    server.wait_for_open_port(80)
    server.succeed("curl -q --fail localhost")
    server.succeed("curl -q --fail localhost/static/admin/js/core.js")
  '';
}
