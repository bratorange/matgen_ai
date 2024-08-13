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
        venvDir = "./.venv";
        pix2pix = pkgs.python3Packages.buildPythonPackage rec {
            pname = "pix2pix";
            version = "1.0";
            src = ./pix2pix;
            pyproject = true;
            build-system = [ pkgs.python3Packages.setuptools ];
            dependencies = with pkgs.python3Packages; [
              torch
              torchvision
              # wandb
            ];
        };
        pythonInterpreter = (pkgs.python3.withPackages (python-pkgs: [
          python-pkgs.numpy
          python-pkgs.pillow
          python-pkgs.flask
          python-pkgs.flask-cors
          python-pkgs.waitress
          pix2pix
        ]));
      in {
        packages.default = pkgs.stdenv.mkDerivation rec {
          name = "matgen-ai";
          version = "1.0";
          src = ./.;

          buildInputs = [  ];

          installPhase = ''
            mkdir -p $out/bin
            cp -r backend.py $out/
            cp -r frontend $out/
            cp -r checkpoints $out/
            echo "#!/bin/sh" > $out/bin/matgen-ai
            echo "exec ${pythonInterpreter}/bin/python $out/backend.py \"\$@\"" >> $out/bin/matgen-ai
            chmod +x $out/bin/matgen-ai
          '';
        };

        packages.debug = pix2pix;
      });
}
