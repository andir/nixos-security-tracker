{ poetry2nix }:
poetry2nix.defaultPoetryOverrides.extend (self: super: {
  cwcwidth = super.cwcwidth.overridePythonAttrs (
    old: {
      nativeBuildInputs = [ super.cython ];
    }
  );
})
