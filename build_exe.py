"""
Script de construção do executável Windows para Mobile-Diag-Pro.

Este script utiliza o PyInstaller para gerar a versão compilada da aplicação.
Suporta modos 'onedir' (padrão) e 'onefile'.

Uso:
    python build_exe.py [--onefile]
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def check_pyinstaller() -> bool:
    """
    Verifica se o PyInstaller está instalado no ambiente atual.

    Returns:
        bool: True se o PyInstaller estiver disponível, False caso contrário.
    """
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def build_executable(onefile: bool = False) -> None:
    """
    Executa a rotina de build do PyInstaller com os parâmetros definidos para o Mobile-Diag-Pro.

    Args:
        onefile (bool): Se True, constrói um único arquivo executável (modo --onefile).
                        Se False, constrói num diretório (modo --onedir).
    """
    if not check_pyinstaller():
        print("Erro: PyInstaller não encontrado!")
        print("Por favor, instale as dependências de build antes de continuar:")
        print("    pip install pyinstaller")
        sys.exit(1)

    import PyInstaller.__main__

    project_root = Path(__file__).parent.resolve()
    main_script = project_root / "main.py"
    
    # Encerrar processos em execução para evitar PermissionError ao sobrescrever DLLs/executáveis
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/f", "/im", "Mobile-Diag-Pro.exe"], capture_output=True)
        except Exception:
            pass

    
    if not main_script.exists():
        print(f"Erro: Script principal '{main_script}' não encontrado.")
        sys.exit(1)

    print(f"Iniciando build do Mobile-Diag-Pro...")
    print(f"Modo: {'Um arquivo (onefile)' if onefile else 'Diretório (onedir)'}")

    # Argumentos base do PyInstaller
    args = [
        str(main_script),
        '--name=Mobile-Diag-Pro',
        '--windowed',  # Sem console
        '--noconfirm',
    ]

    # Modo de distribuição
    if onefile:
        args.append('--onefile')
    else:
        args.append('--onedir')

    # Adicionar recursos (assets)
    # Formato no Windows é origem;destino
    assets_dir = project_root / "assets"
    if assets_dir.exists():
        args.append(f'--add-data={assets_dir};assets')
    else:
        print("Aviso: Diretório de assets não encontrado. O executável pode não ter ícones/recursos visuais.")

    scripts_dir = project_root / "scripts"
    if scripts_dir.exists():
        args.append(f'--add-data={scripts_dir};scripts')

    inf_file = project_root / "fastboot_jlq.inf"
    if inf_file.exists():
        args.append(f'--add-data={inf_file};.')

    # Imports ocultos necessários para Qt e telemetria
    hidden_imports = [
        'pyqtgraph',
        'pyqtgraph.graphicsItems',
        'psutil',
        'toml',
        'darkdetect',
        'packaging',
        'cryptography'
    ]
    for imp in hidden_imports:
        args.append(f'--hidden-import={imp}')

    # Excluir módulos pesados não utilizados na aplicação
    exclude_modules = [
        'torch', 'torchvision', 'torchaudio', 'scipy', 'pandas', 
        'matplotlib', 'tkinter', 'IPython', 'jupyter', 'sklearn', 
        'cv2', 'tensorboard', 'win32com', 'pytest'
    ]
    for exc in exclude_modules:
        args.append(f'--exclude-module={exc}')

    # Diretório temporário de saída para evitar bloqueio do Windows Explorer na pasta dist
    build_dist = project_root / "dist_build"
    args.append(f'--distpath={build_dist}')

    # Executa o PyInstaller
    try:
        PyInstaller.__main__.run(args)
    except Exception as e:
        print(f"Erro durante o processo de build: {e}")
        sys.exit(1)

    # Resumo final e sincronização com dist/
    dist_dir = project_root / "dist"
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    if sys.platform == "win32":
        try:
            subprocess.run(["taskkill", "/f", "/im", "Mobile-Diag-Pro.exe"], capture_output=True)
        except Exception:
            pass

    import shutil
    if onefile:
        built_exe = build_dist / "Mobile-Diag-Pro.exe"
        target_exe = dist_dir / "Mobile-Diag-Pro.exe"
        if built_exe.exists():
            shutil.copy2(built_exe, target_exe)
        exe_path = target_exe
        print("\n" + "="*50)
        print("BUILD CONCLUÍDO COM SUCESSO!")
        print("="*50)
        print(f"Localização do executável: {exe_path}")
        print("\nPróximos passos:")
        print("1. O arquivo .exe já está pronto para uso e distribuição.")
    else:
        built_app_dir = build_dist / "Mobile-Diag-Pro"
        target_app_dir = dist_dir / "Mobile-Diag-Pro"
        if built_app_dir.exists():
            shutil.copytree(built_app_dir, target_app_dir, dirs_exist_ok=True)
        exe_path = target_app_dir / "Mobile-Diag-Pro.exe"
        print("\n" + "="*50)
        print("BUILD CONCLUÍDO COM SUCESSO!")
        print("="*50)
        print(f"Diretório da aplicação: {target_app_dir}")
        print(f"Executável principal: {exe_path}")
        print("\nPróximos passos para distribuição:")
        print("1. Crie um arquivo ZIP do diretório 'Mobile-Diag-Pro' para uma versão portátil.")
        print("2. Ou utilize o script Inno Setup (scripts/create_installer.iss) para gerar um instalador.")
    print("="*50 + "\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Construir executável do Mobile-Diag-Pro")
    parser.add_argument("--onefile", action="store_true", help="Construir um único arquivo executável (default é onedir)")
    args = parser.parse_args()
    
    build_executable(args.onefile)
