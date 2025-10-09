rec {
  description = "Local OCR helper, primarily intended for reading visual novels in Japanese.";

  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
  };

  outputs =
    { self, nixpkgs, ... }:
    let
      inherit (nixpkgs) lib;
      forAllSystems = lib.genAttrs lib.systems.flakeExposed;
    in
    {
      devShells = forAllSystems (
        system:
        let
          pkgs = nixpkgs.legacyPackages.${system};
        in
        {
          default = pkgs.mkShell {
            packages = with pkgs; [
              virtualenv
              tokei # Line counting
            ];
            inputsFrom = with self.packages.${system}; [ yomite ];
          };
        }
      );

      packages = forAllSystems (system: let
        pkgs = nixpkgs.legacyPackages.${system};
      in {
        default = self.packages.${system}.yomite;
        yomite = pkgs.python3.pkgs.buildPythonApplication {
          pname = "yomite";
          version = "0.1.0";
          pyproject = true;
          build-system = with pkgs.python3.pkgs; [ setuptools ];

          src = ./.;

          propagatedBuildInputs = with pkgs.python3.pkgs; [
            flask
            numpy
            pillow
            pytesseract
          ] ++ (with pkgs; [
            tesseract # OCR
            # screen area selection
            slurp # Wayland
            slop # X11
          ]);

          preBuild = ''
            echo -e "from setuptools import setup\nsetup(scripts=['src/__main__.py'])" > setup.py
          '';

          postInstall = let
            desktop = pkgs.makeDesktopItem {
              name = "yomite";
              genericName = "OCR helper";
              desktopName = "yomite";
              exec = "yomite";
              icon = "book";
              comment = description;
            };
          in ''
            pushd $out/bin
            mv __main__.py yomite
            cp -r ${./src/static} static
            cp -r ${./src/templates} templates
            popd

            mkdir -p $out/share/applications
            cp ${desktop}/share/applications/* $out/share/applications
          '';

          meta = with lib; {
            description = description;
            homepage = "https://github.com/ElnuDev/yomite";
            license = licenses.gpl3Only;
            mainProgram = "yomite";
            maintainers = with maintainers; [ elnudev ];
            platforms = lib.platforms.linux;
          };
        };
      });
    };
}