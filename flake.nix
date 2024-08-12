{
  description = "MatGen AI Application";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, flake-utils }:
    flake-utils.lib.eachDefaultSystem (system:
      let
        pkgs = nixpkgs.legacyPackages.${system};
        python = pkgs.python3;
        venvDir = "./.venv";
        pythonEnv = pkgs.stdenv.mkDerivation {
            src = ./.;
            name = "matgen-ai-env";
            buildInputs = [ python python.pkgs.pip ];
            buildPhase = ''
              python -m venv venv
              source venv/bin/activate
              pip install -r requirements.txt
            '';
            installPhase = ''
              cp -r venv $out/
            '';

        };
      in
      {
        packages.default = pkgs.stdenv.mkDerivation {
          name = "matgen-ai";
          version = "1.0";
          src = ./.;

          buildInputs = [
            pythonEnv
          ];

          installPhase = ''
            mkdir -p $out/bin
            cp -r backend.py $out/
            cp -r frontend $out/
            echo "#!/bin/sh" > $out/bin/matgen-ai
            echo "source $out/${pythonEnv}/bin/activate" >> $out/bin/matgen-ai
            echo "exec $out/${pythonEnv}/bin/python $out/backend.py \"\$@\"" >> $out/bin/matgen-ai
            chmod +x $out/bin/matgen-ai
          '';
        };

        apps.default = flake-utils.lib.mkApp {
          drv = self.packages.${system}.default;
        };
      }
    );
}
