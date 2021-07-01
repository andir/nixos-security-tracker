{ pkgs ? import ./nix }:
let
  sharedSecret = "1234567890123456789012345";

  testSecretKey = "my-amazing-secret-key";
  testAccessKey = "my-amazing-access-key";
  common = {
    virtualisation.memorySize = 1024;
    imports = [ ./module.nix ];
    services.nixos-security-tracker.enable = true;
    # Increase the timeout to 90s as GitHub Actions is SLOW
    services.nixos-security-tracker.workerTimeout = 90;
    services.nginx.appendHttpConfig = "proxy_read_timeout 90;";

    # enable minio in the tests to verify the S3 channel import
    services.minio = {
      enable = true;
      secretKey = testSecretKey;
      accessKey = testAccessKey;
    };

    # configure the import channels unit to start after minio and with the correct access keys
    systemd.services.nixos-security-tracker-import-channels = {
      after = [ "minio.service" ];
      wants = [ "minio.service" ];
      environment = {
        AWS_S3_ENDPOINT_URL = "http://localhost:9000"; # minio
        AWS_SECRET_ACCESS_KEY = testSecretKey;
        AWS_ACCESS_KEY_ID = testAccessKey;
        DJANGO_LOG_LEVEL = "DEBUG";
      };
    };

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
        cat ${./tracker/github_events/signature.py} > script.py
        cat - <<EOF >> script.py
        print(compute_github_hmac("${sharedSecret}".encode(), open("$githubEventPath", "rb").read()))
        EOF

        python script.py > $out
      '';

      # helper script to setup the minio buckets
      createNixReleaseBucket =
        let
          releaseBucketContent = pkgs.linkFarm "nix-releases" [
            {
              name = "nixos/nixos-42.23";
              path = pkgs.linkFarm "nixos-42.23" [
                { name = "git-revision"; path = pkgs.writeText "git-revision" "12346"; }
                {
                  name = "packages.json.br";
                  # This synthesizes the packages.json file as is done within nixpkgs.
                  # We are using the channel revision that is pinned in this project. This should give use sufficient test data.
                  path = pkgs.runCommand "packages.json.br" { nativeBuildInputs = [ pkgs.brotli pkgs.nix ]; nixpkgs = pkgs.path; } ''
                    export NIX_STATE_DIR=$TMPDIR
                    export NIX_PATH=$TMPDIR/asfdasdf
                    echo '{"version": 2, "packages": ' > packages.json
                    nix-env -f $nixpkgs -I nixpkgs=$nixpkgs -qa --json | sed -e "s|$nixpkgs/||g" >> packages.json
                    echo '}' >> packages.json
                    brotli -9 < packages.json > $out
                  '';
                }
              ];
            }
          ];
        in
        pkgs.writeShellScript "create-nix-release-bucket" ''
          PATH="${pkgs.minio-client}/bin:$PATH"
          set -exuo pipefail
          mc alias set minio http://localhost:9000 ${testAccessKey} ${testSecretKey}
          mc mb minio/nix-releases

          # for minio to accept the data it can not be in the nix store as otherwise `mc cp` fails
          # with an error saying that it can't verify the source of the files.
          cp -Lr ${releaseBucketContent} /root/nix-releases
          mc cp -r /root/nix-releases/nixos minio/nix-releases/
          rm -rf /root/nix-releases
          mc policy list minio/nix-releases
          mc policy set public minio/nix-releases
        '';

      # Verify that we can access the bucket with the configured credentials using the
      # official AWS cli.
      verifyNixReleaseBucket = pkgs.writeShellScript "verify-nix-release-bucket" ''
        set -exuo pipefail
        PATH="${pkgs.awscli2}/bin:$PATH"
        export AWS_SECRET_ACCESS_KEY="${testSecretKey}"
        export AWS_ACCESS_KEY_ID="${testAccessKey}"

        s3="aws s3 --endpoint-url http://localhost:9000"
        $s3 ls s3://nix-releases/nixos/nixos-42.23/
        $s3 cp s3://nix-releases/nixos/nixos-42.23/packages.json.br /tmp/trash
        $s3 cp s3://nix-releases/nixos/nixos-42.23/git-revision /tmp/trash
        rm /tmp/trash
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

        with subtest("Import Channels"):
          # use the local minio server to simulate the NIX release buckets so we can import a deterministic channel description within a pure test.
          server.succeed("${createNixReleaseBucket}")
          # verify that the bucket exists and has the right shape
          server.succeed("${verifyNixReleaseBucket}")
          server.succeed("systemctl start --wait nixos-security-tracker-import-channels.service")

        server.shutdown()


      test_server(sqlite)
      test_server(postgresql, signatureFile="${signatureFile}")
    '';
}
