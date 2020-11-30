{ pkgs ? import ./nix }:
let
  src = pkgs.gitignoreSource ./.;
  pre-commit-hooks = pkgs.nix-pre-commit-hooks.run {
    inherit src;
    hooks = {
      nixpkgs-fmt.enable = true;
      black.enable = true;
      isort = {
        enable = true;
        entry = "${env}/bin/isort --apply --atomic";
        pass_filenames = true;
      };
      django-migration-check = {
        enable = true;
        entry = "${env}/bin/python manage.py makemigrations --check --dry-run";
        pass_filenames = false;
      };
      editorconfig = {
        enable = true;
        entry = "${pkgs.editorconfig-checker}/bin/editorconfig-checker '\\.git'";
        pass_filenames = false;
      };
      bandit = {
        enable = true;
        entry = "${env}/bin/bandit -r ";
        pass_filenames = true;
      };
    };
  };
  env = pkgs.poetry2nix.mkPoetryEnv {
    python = pkgs.python3;
    pyproject = ./pyproject.toml;
    poetrylock = ./poetry.lock;
    overrides = pkgs.callPackage ./nix/python-overrides.nix { };
  };

  test-runner = pkgs.writeShellScriptBin "test-runner" ''
    find . -type f -iname '*.py' | ${pkgs.entr}/bin/entr -cr python manage.py test "$@"
  '';

in
pkgs.mkShell {
  nativeBuildInputs = [
    env
    pkgs.nixpkgs-fmt
    pkgs.niv
    pkgs.git
    pkgs.poetry
    pkgs.python3Packages.black
    pkgs.python3Packages.mypy
    pkgs.python3Packages.flake8
    pkgs.geckodriver
    pkgs.firefox
    pkgs.netlify-cli
    test-runner
  ];

  NIXOS_SECURITY_TRACKER_DEBUG = "1";

  inherit (pre-commit-hooks) shellHook;
}
