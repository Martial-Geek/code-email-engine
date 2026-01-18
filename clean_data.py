"""
Clean all processed data folders (keeps data/raw intact).
Removes all files from:
- data/cleaned/
- data/enriched/
- data/scored/
- data/emails/
- data/final/
"""

import shutil
from pathlib import Path
from rich.console import Console

console = Console()


def clean_data_folders():
    """Remove all processed data files while keeping raw data."""
    
    base_dir = Path(__file__).parent / 'data'
    
    # Folders to clean
    folders_to_clean = [
        base_dir / 'cleaned',
        base_dir / 'enriched',
        base_dir / 'scored',
        base_dir / 'emails',
        base_dir / 'final',
    ]
    
    console.print("\n[bold yellow]Cleaning processed data folders...[/bold yellow]\n")
    
    total_removed = 0
    
    for folder in folders_to_clean:
        if not folder.exists():
            console.print(f"[dim]Skipping {folder.name}/ (doesn't exist)[/dim]")
            continue
        
        files = list(folder.glob('*'))
        file_count = len(files)
        
        if file_count == 0:
            console.print(f"[dim]✓ {folder.name}/ (already empty)[/dim]")
            continue
        
        # Remove all files
        for file in files:
            if file.is_file():
                file.unlink()
        
        total_removed += file_count
        console.print(f"[green]✓ {folder.name}/ (removed {file_count} files)[/green]")
    
    console.print(f"\n[bold green]Done! Removed {total_removed} files total.[/bold green]")
    console.print(f"[dim]data/raw/ remains untouched[/dim]\n")


if __name__ == "__main__":
    clean_data_folders()
