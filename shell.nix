{ pkgs ? import ./nix }:
let
  src = pkgs.gitignoreSource ./.;
  pre-commit-hooks = pkgs.nix-pre-commit-hooks.run {
    inherit src;
    hooks = {
      nixpkgs-fmt.enable = true;
      black.enable = true;
    };
  };
  env = pkgs.poetry2nix.mkPoetryEnv {
    python = pkgs.python3;
    pyproject = ./pyproject.toml;
    poetrylock = ./poetry.lock;
  };


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
    pkgs.python3Packages.isort
  ];

  inherit (pre-commit-hooks) shellHook;
}
