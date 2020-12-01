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

  sharedSecret = "1234567890123456789012345";
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

      # In the postgresql case we also verify that the github receive hook
      # verifies signatures.
      # Do not do this in production. You should not have the secret in your
      # Nix store!
      services.nixos-security-tracker.githubEventsSharedSecretFile = toString (pkgs.writeText "shared-secret" sharedSecret);
    };
  };
  testScript =
    let
      githubEvent = builtins.toJSON {
        some = "githubEvent";
      };

      # use our python code to calculate the signature for our test message
      signatureFile = pkgs.runCommand "calculate-signature"
        {
          inherit githubEvent;
          passAsFile = [ "githubEvent" ];
          buildInputs = [
            pkgs.python3
          ];
        } ''
        cat ${./tracker/utils.py} > script.py
        cat - <<EOF >> script.py
        print(compute_github_hmac("${sharedSecret}".encode(), open("$githubEventPath", "rb").read()))
        EOF

        python script.py > $out
      '';

      githubEventFile = pkgs.writeText "githubEvent" githubEvent;
    in
    ''
      # fmt: off
      def test_server(server, signatureFile=False):
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

        with subtest("GitHub Events"):
            # if we have a valid signature for pushing GitHub events verify
            # that it is required & that it actaully works when used
            if signatureFile:
                signature = open(signatureFile).read().strip()
                # first try without a token, must fail
                server.fail("curl -s --fail localhost/__github_event -d @${githubEventFile} -H 'X-GitHub-Event: test' -H")
                # then try with an invalid toke, also must fail
                server.fail("curl -s --fail localhost/__github_event -d @${githubEventFile} -H 'X-GitHub-Event: test' -H 'X-Hub-Signature: lalalalala'")
                # finally try with a valid tokne, must succeed
                server.succeed(f"curl -s --fail localhost/__github_event -d @${githubEventFile} -H 'X-GitHub-Event: test' -H 'X-Hub-Signature: {signature}'")
            else:
                # otherwise we must succeed pushing an event without a signature (or a random signature we are not validating then)
                server.succeed("curl -s --fail localhost/__github_event -d @${githubEventFile} -H 'X-GitHub-Event: test'")
                server.succeed("curl -s --fail localhost/__github_event -d @${githubEventFile} -H 'X-GitHub-Event: test' -H 'X-Hub-Signature: a random signature'")

            server.shutdown()

      test_server(sqlite)
      test_server(postgresql, signatureFile="${signatureFile}")
    '';
}
