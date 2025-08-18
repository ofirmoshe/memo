import logging
from sqlalchemy import inspect, text

logger = logging.getLogger(__name__)

NEW_COLUMNS = [
	("content_text", "TEXT"),
	("content_json", "JSON"),
	("preview_image_url", "VARCHAR(512)"),
	("preview_thumbnail_path", "VARCHAR(512)")
]

def check_migration_needed(engine) -> bool:
	"""Return True if any of the new columns are missing on items table."""
	insp = inspect(engine)
	columns = {col["name"] for col in insp.get_columns("items")}
	needed = any(name not in columns for name, _ in NEW_COLUMNS)
	return needed


def run_migration(engine, action: str = "apply") -> bool:
	"""Apply migration: add new columns if they don't exist. No-op on revert."""
	if action != "apply":
		logger.info("Revert not implemented for add_item_fields migration")
		return True
	
	try:
		insp = inspect(engine)
		existing = {col["name"] for col in insp.get_columns("items")}
		with engine.begin() as conn:
			for name, ddl_type in NEW_COLUMNS:
				if name not in existing:
					logger.info(f"Adding column '{name}' to items table")
					conn.execute(text(f"ALTER TABLE items ADD COLUMN {name} {ddl_type}"))
		logger.info("add_item_fields migration applied successfully")
		return True
	except Exception as e:
		logger.error(f"Failed to apply add_item_fields migration: {e}")
		return False 