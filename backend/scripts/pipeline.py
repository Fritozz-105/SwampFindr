"""Pipeline orchestrator: run listing ingestion and/or embedding."""
import argparse
import subprocess
import sys
import os


def run_ingestion():
  """Run the listing ingestion script."""
  print("Running listing ingestion")
  script = os.path.join(os.path.dirname(__file__), "listings.py")
  result = subprocess.run([sys.executable, script], cwd=os.path.dirname(__file__))
  if result.returncode != 0:
    print("Ingestion failed.")
    sys.exit(1)

  print("Ingestion complete.")


def run_embedding():
  """Run the embedding script."""
  print("Running listing embedding")

  # Import directly so we share the same process/env
  sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
  from scripts.embed_listings import embed_all_listings
  embed_all_listings()
  print("Embedding complete.")


def main():
  parser = argparse.ArgumentParser(description="SwampFindr data pipeline")
  parser.add_argument(
    "--skip-embed",
    action="store_true",
    help="Run ingestion only, skip embedding",
  )
  parser.add_argument(
    "--embed-only",
    action="store_true",
    help="Skip ingestion, only embed existing MongoDB listings",
  )
  args = parser.parse_args()

  if args.skip_embed and args.embed_only:
    print("Error: cannot use both --skip-embed and --embed-only")
    sys.exit(1)

  if not args.embed_only:
    run_ingestion()

  if not args.skip_embed:
    run_embedding()

  print("Pipeline complete.")


if __name__ == "__main__":
  main()
