{ pkgs ? import ./nix }:
let
  cleanSource = src: pkgs.lib.cleanSourceWith (rec {
    name = "src";
    inherit src;
    filter =
      let
        srcIgnored = pkgs.gitignore-nix.gitignoreFilter src;
      in
      name: type:
        let
          base = builtins.baseNameOf name;
        in
        srcIgnored name type
        && ! (type == "regular" && pkgs.lib.hasSuffix ".nix" name)
        && !(type == "directory" && base == ".github")
    ;
  });
  src = cleanSource ./.;
  pkg = pkgs.poetry2nix.mkPoetryApplication {
    inherit src;
    projectDir = src;
    python = pkgs.python3;
    overrides = pkgs.callPackage ./nix/python-overrides.nix { };
    checkPhase = ''
      SKIP_E2E_TESTS=1 pytest .

      # test that migrations actually work & are up to date
      python manage.py makemigrations --check
      python manage.py migrate
    '';
  };
  env = pkg.python.withPackages (_: [ pkg ]);

  manage = pkgs.writeShellScriptBin "manage" ''
    PATH=${env}/bin:$PATH
    exec python ${src + "/manage.py"} "$@"
  '';

  staticFiles = pkgs.runCommand "static-files"
    {
      buildInputs = [ manage ];
      NIXOS_SECURITY_TRACKER_STATIC_ROOT = placeholder "out";
    } ''
    mkdir $out
    cd $out
    echo yes | manage collectstatic
  '';
in
pkg // {
  inherit manage staticFiles env;
  asgiPath = "nixos_security_tracker.asgi:application";
  wsgiPath = "nixos_security_tracker.wsgi:application";
}
