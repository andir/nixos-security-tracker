{ poetry2nix }:
poetry2nix.defaultPoetryOverrides.extend (self: super: {
  packaging = super.packaging.overridePythonAttrs (
    old: {
      # packaging now requires flit_core to be built:
      # https://github.com/nix-community/poetry2nix/issues/218
      buildInputs = [ super.flit-core ];
    }
  );
})
