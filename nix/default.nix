let
  sources = import ./sources.nix;
  overlays = [
    (self: super: {
      nix-pre-commit-hooks = import (sources.nix-pre-commit-hooks);

      poetry2nix = self.callPackage (sources.poetry2nix) { };

      gitignore-nix = self.callPackage (sources."gitignore.nix") { };
    })
  ];
in
import sources.nixpkgs {
  inherit overlays;
}
