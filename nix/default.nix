let
  sources = import ./sources.nix;
  overlays = [
    (self: super: {
      nix-pre-commit-hooks = import (sources.nix-pre-commit-hooks);

      poetry2nix = self.callPackage (sources.poetry2nix) { };

      gitignore-nix = self.callPackage (sources."gitignore.nix") { };

      netlify_deployer = self.python3Packages.buildPythonApplication rec {
        pname = "netlify_deployer";
        version = "0.5.2";
        src = super.python3Packages.fetchPypi {
          inherit pname version;
          sha256 = "0vmfvwyiwrw5rh3imfn8xjndl7khdi29n9kkmn0q4h776qmhkq5a";
        };
        postPatch = ''
          # https://github.com/cyplo/netlify_deployer/pull/5
          sed -e 's/hello_world/main/g' -i netlify_deployer/__main__.py

          # Correct the environment variable so it is compatible with netlify-cli
          sed -e 's/"NETLIFY_TOKEN"/"NETLIFY_AUTH_TOKEN"/g' -i netlify_deployer/__init__.py
        '';
        propagatedBuildInputs = [ self.python3Packages.requests ];
        nativeBuildInputs = [ self.python3Packages.pbr ];

        postCheck = ''
          stat $out/bin/netlify-deployer > /dev/null
        '';
      };
    })
  ];
in
import sources.nixpkgs {
  inherit overlays;
}
