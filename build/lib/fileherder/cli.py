"""
Command-line interface for fileherder using Rich.

Provides an interactive, visually appealing CLI for all file management
operations with progress bars, tables, and colors.

Author: Luke Steuber
"""

import sys
import argparse
import logging
from pathlib import Path
from typing import Optional

try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
    from rich.panel import Panel
    from rich.prompt import Confirm
    from rich import print as rprint
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None

from .core import FileHerder, DuplicateGroup
from .operations import delete_files_safe, format_size

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# CLI Application
# ============================================================================

class FileHerderCLI:
    """
    Rich-powered CLI for fileherder operations.

    Example:
        >>> cli = FileHerderCLI()
        >>> cli.find_duplicates_command("/data", min_size=1024*1024)
    """

    def __init__(self):
        """Initialize CLI with Rich console."""
        if RICH_AVAILABLE:
            self.console = Console()
        else:
            self.console = None
            print("WARNING: Rich library not available. Install with: pip install rich")

        self.herder = FileHerder()

    def print(self, *args, **kwargs):
        """Print using Rich if available, else regular print."""
        if self.console:
            self.console.print(*args, **kwargs)
        else:
            print(*args, **kwargs)

    def find_duplicates_command(
        self,
        directory: str,
        recursive: bool = True,
        min_size: int = 0,
        extensions: Optional[str] = None,
        delete: bool = False
    ):
        """
        Find and display duplicate files.

        Args:
            directory: Directory to scan
            recursive: Scan subdirectories
            min_size: Minimum file size in bytes
            extensions: Comma-separated list of extensions (e.g., ".jpg,.png")
            delete: Interactively delete duplicates
        """
        dir_path = Path(directory)

        if not dir_path.is_dir():
            self.print(f"[red]Error: Invalid directory: {directory}[/red]")
            return 1

        # Parse extensions if provided
        ext_set = None
        if extensions:
            ext_set = {ext.strip() for ext in extensions.split(',')}

        # Show scanning message
        self.print("\n[bold cyan]Scanning for duplicates...[/bold cyan]")

        # Find duplicates
        duplicates = self.herder.find_duplicates(
            dir_path,
            recursive=recursive,
            min_size=min_size,
            extensions=ext_set
        )

        if not duplicates:
            self.print("[green]No duplicates found![/green]")
            return 0

        # Display results in table
        self._display_duplicates_table(duplicates)

        # Calculate totals
        total_groups = len(duplicates)
        total_duplicates = sum(g.count - 1 for g in duplicates)  # Exclude originals
        total_waste = sum(g.waste_size for g in duplicates)

        self.print(f"\n[bold]Summary:[/bold]")
        self.print(f"  Duplicate groups: {total_groups}")
        self.print(f"  Duplicate files: {total_duplicates}")
        self.print(f"  Wasted space: [red]{format_size(total_waste)}[/red]")

        # Offer to delete duplicates
        if delete and self.console:
            if Confirm.ask("\nDelete duplicate files (keeping one copy of each)?"):
                self._delete_duplicates_interactive(duplicates)

        return 0

    def _display_duplicates_table(self, duplicates: list[DuplicateGroup]):
        """Display duplicates in a Rich table."""
        if not self.console:
            # Fallback: plain text
            for i, group in enumerate(duplicates, 1):
                print(f"\nGroup {i} ({group.count} files, {format_size(group.waste_size)} wasted):")
                for file_path in group.files:
                    print(f"  - {file_path}")
            return

        table = Table(title="Duplicate Files Found", show_header=True, header_style="bold magenta")
        table.add_column("Group", style="cyan", width=6)
        table.add_column("Hash (first 8)", style="dim")
        table.add_column("Files", justify="right", style="yellow")
        table.add_column("Wasted Space", justify="right", style="red")
        table.add_column("Example File", style="green")

        for i, group in enumerate(duplicates[:20], 1):  # Show top 20
            table.add_row(
                str(i),
                group.hash_value[:8],
                str(group.count),
                format_size(group.waste_size),
                group.files[0].name
            )

        if len(duplicates) > 20:
            table.add_row(
                "...",
                "...",
                "...",
                "...",
                f"... and {len(duplicates) - 20} more groups"
            )

        self.console.print(table)

    def _delete_duplicates_interactive(self, duplicates: list[DuplicateGroup]):
        """Interactively delete duplicate files, keeping one copy."""
        files_to_delete = []

        for group in duplicates:
            # Keep first file, delete the rest
            files_to_delete.extend(group.files[1:])

        self.print(f"\n[yellow]About to delete {len(files_to_delete)} duplicate files[/yellow]")
        self.print("[green]Keeping the first occurrence of each file[/green]")

        result = delete_files_safe(
            files_to_delete,
            require_confirmation=True,
            dry_run=False
        )

        if result.success:
            self.print(f"\n[green]✓ Successfully deleted {result.success_count} files[/green]")
        else:
            self.print(f"\n[yellow]Deleted {result.success_count} files with {result.failure_count} errors[/yellow]")
            if result.errors:
                self.print("\n[red]Errors:[/red]")
                for path, error in result.errors[:10]:
                    self.print(f"  - {path}: {error}")

    def organize_command(
        self,
        directory: str,
        dry_run: bool = False
    ):
        """
        Organize directory by file type.

        Args:
            directory: Directory to organize
            dry_run: Simulate without making changes
        """
        dir_path = Path(directory)

        if not dir_path.is_dir():
            self.print(f"[red]Error: Invalid directory: {directory}[/red]")
            return 1

        mode = "[yellow]DRY RUN[/yellow]" if dry_run else "[green]ORGANIZING[/green]"
        self.print(f"\n{mode} directory: {directory}")

        # Organize
        result = self.herder.organize(dir_path, dry_run=dry_run)

        if not result.success:
            self.print(f"[red]Error: {result.error}[/red]")
            return 1

        # Display results in table
        self._display_organization_table(result.category_counts)

        self.print(f"\n[bold]Summary:[/bold]")
        self.print(f"  Files organized: {result.files_organized}")
        self.print(f"  Categories: {len(result.categories_created)}")

        return 0

    def _display_organization_table(self, category_counts: dict[str, int]):
        """Display organization results in a Rich table."""
        if not self.console:
            # Fallback: plain text
            print("\nFile Type Distribution:")
            for category, count in sorted(category_counts.items()):
                print(f"  {category}: {count} files")
            return

        table = Table(title="File Type Distribution", show_header=True, header_style="bold magenta")
        table.add_column("Category", style="cyan")
        table.add_column("Files", justify="right", style="yellow")

        # Sort by count (descending)
        sorted_categories = sorted(category_counts.items(), key=lambda x: x[1], reverse=True)

        for category, count in sorted_categories:
            table.add_row(category, str(count))

        self.console.print(table)

    def stats_command(self, directory: str):
        """
        Show directory statistics.

        Args:
            directory: Directory to analyze
        """
        dir_path = Path(directory)

        if not dir_path.is_dir():
            self.print(f"[red]Error: Invalid directory: {directory}[/red]")
            return 1

        self.print("\n[bold cyan]Analyzing directory...[/bold cyan]")

        # Get statistics
        stats = self.herder.get_statistics(dir_path)

        if 'error' in stats:
            self.print(f"[red]Error: {stats['error']}[/red]")
            return 1

        # Display summary
        if self.console:
            panel = Panel(
                f"[bold]Total Files:[/bold] {stats['total_files']}\n"
                f"[bold]Total Size:[/bold] {stats['total_size_mb']:.2f} MB\n"
                f"[bold]File Types:[/bold] {len(stats['types'])}",
                title="Directory Statistics",
                border_style="cyan"
            )
            self.console.print(panel)
        else:
            print(f"\nDirectory Statistics:")
            print(f"  Total Files: {stats['total_files']}")
            print(f"  Total Size: {stats['total_size_mb']:.2f} MB")
            print(f"  File Types: {len(stats['types'])}")

        # Display type breakdown
        self._display_organization_table(stats['types'])

        # Display largest files
        if stats['largest_files']:
            self.print("\n[bold]Largest Files:[/bold]")
            for item in stats['largest_files'][:10]:
                size_str = format_size(item['size'])
                self.print(f"  {size_str:>12}  {Path(item['path']).name}")

        return 0


# ============================================================================
# Main Entry Point
# ============================================================================

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="fileherder - Lightweight File Management Utilities",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Find duplicates larger than 1MB
  fileherder duplicates /data --min-size 1048576

  # Find duplicate images
  fileherder duplicates /photos --extensions .jpg,.png

  # Organize directory by file type
  fileherder organize /downloads

  # Dry run (simulate) organization
  fileherder organize /downloads --dry-run

  # Show directory statistics
  fileherder stats /data

MIT License by Luke Steuber
        """
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Duplicates command
    dup_parser = subparsers.add_parser("duplicates", help="Find duplicate files")
    dup_parser.add_argument("directory", help="Directory to scan")
    dup_parser.add_argument("--recursive", action="store_true", default=True,
                            help="Scan subdirectories (default: True)")
    dup_parser.add_argument("--min-size", type=int, default=0,
                            help="Minimum file size in bytes")
    dup_parser.add_argument("--extensions", type=str,
                            help="Comma-separated extensions (e.g., .jpg,.png)")
    dup_parser.add_argument("--delete", action="store_true",
                            help="Interactively delete duplicates")

    # Organize command
    org_parser = subparsers.add_parser("organize", help="Organize files by type")
    org_parser.add_argument("directory", help="Directory to organize")
    org_parser.add_argument("--dry-run", action="store_true",
                            help="Simulate without making changes")

    # Stats command
    stats_parser = subparsers.add_parser("stats", help="Show directory statistics")
    stats_parser.add_argument("directory", help="Directory to analyze")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Create CLI instance
    cli = FileHerderCLI()

    # Execute command
    if args.command == "duplicates":
        return cli.find_duplicates_command(
            args.directory,
            recursive=args.recursive,
            min_size=args.min_size,
            extensions=args.extensions,
            delete=args.delete
        )

    elif args.command == "organize":
        return cli.organize_command(
            args.directory,
            dry_run=args.dry_run
        )

    elif args.command == "stats":
        return cli.stats_command(args.directory)

    return 0


if __name__ == "__main__":
    sys.exit(main())
