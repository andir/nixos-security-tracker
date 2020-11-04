let
  sources = import ./sources.nix;
  overlays = [
    (self: super: {
      inherit (self.callPackage sources.gitignore { }) gitignoreSource;
      nix-pre-commit-hooks = import (sources.nix-pre-commit-hooks);

      poetry2nix = self.callPackage (sources.poetry2nix) { };
    })
  ];
in
import sources.nixpkgs {
  inherit overlays;
}
