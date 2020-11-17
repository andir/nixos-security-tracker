# Script that is being run within the GitHub Actions to publish our test results (to netlify and the PR)
let
  pkgs = import ../../nix;

  env = pkgs.buildEnv {
    name = "publish-test-results-script";
    paths = [ pkgs.netlify-cli pkgs.jq pkgs.coreutils pkgs.curl ];
  };

in
pkgs.writeShellScript "publish-test-results" ''
    PATH=${env}/bin
    set -ex
    args="--dir=coverage-report --json"

    if [[ "''${GITHUB_REF}" == "master" ]]; then
     args="$args --prod"
    fi

    netlify deploy $args | tee netlify.json

    if [[ "$GITHUB_EVENT_NAME" == "pull_request" ]]; then
      DEPLOYED_URL=$(jq -r .deploy_url netlify.json)
      PR_NUMBER=$(jq -r .number "$GITHUB_EVENT_PATH")
      cat << EOF >/tmp/body.txt
  PyTest Coverage report has been published to $DEPLOYED_URL.
  Test results:

  \`\`\`
        $(cat pytest.log)
  \`\`\`
  EOF

      jq -n --rawfile body /tmp/body.txt '.body = $body' > /tmp/body.json

      curl \
        -X POST \
        -H "Accept: application/vnd.github.v3+json" \
        -H "Authorization: Bearer $GITHUB_TOKEN" \
            ''${GITHUB_API_URL}/repos/''${GITHUB_REPOSITORY}/issues/$PR_NUMBER/comments \
        -d @/tmp/body.json
     fi

''
