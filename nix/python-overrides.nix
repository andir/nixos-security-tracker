{ poetry2nix }:
poetry2nix.defaultPoetryOverrides.extend (self: super: {
  cwcwidth = super.cwcwidth.overridePythonAttrs (
    old: {
      nativeBuildInputs = [ super.cython ];
    }
  );
  # see https://github.com/nix-community/poetry2nix/issues/323
  mypy = super.mypy.overridePythonAttrs (oa: {
    MYPY_USE_MYPYC = false;
  });
})
