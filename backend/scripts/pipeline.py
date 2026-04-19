"""Pipeline orchestrator: run listing ingestion, embedding, and/or image enhancement"""
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


def run_enhancement():
  """Run the image enhancement script (requires 'enhance' extras)."""
  print("Running image enhancement")
  sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
  from scripts.img_enhance import process_listings_images
  process_listings_images()
  print("Image enhancement complete.")


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
  parser.add_argument(
    "--skip-enhance",
    action="store_true",
    help="Skip image enhancement step",
  )
  parser.add_argument(
    "--enhance-only",
    action="store_true",
    help="Skip ingestion and embedding, only enhance images",
  )
  args = parser.parse_args()

  if args.skip_embed and args.embed_only:
    print("Error: cannot use both --skip-embed and --embed-only")
    sys.exit(1)

  if args.enhance_only:
    run_enhancement()
    print("Pipeline complete.")
    return

  if not args.embed_only:
    run_ingestion()

  if not args.skip_embed:
    run_embedding()

  if not args.skip_enhance:
    run_enhancement()

  print("Pipeline complete.")


if __name__ == "__main__":
  main()
