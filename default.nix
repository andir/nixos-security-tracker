{ pkgs ? import ./nix }:
pkgs.poetry2nix.mkPoetryApplication {
  src = pkgs.gitignoreSource ./.;
  projectDir = ./.;
  python = pkgs.python3;
}
