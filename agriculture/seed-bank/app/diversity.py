"""Genetic diversity analysis and alerts."""

from fastapi import APIRouter, Query

from .database import query

router = APIRouter(prefix="/api/diversity", tags=["diversity"])


@router.get("/scores")
def diversity_scores(min_sources: int = Query(3, description="Minimum sources for healthy diversity")) -> list[dict]:
    """Calculate genetic diversity score per crop species."""
    rows = query("""
        SELECT species,
               COUNT(*) as total_lots,
               COUNT(DISTINCT source) as distinct_sources,
               SUM(quantity) as total_quantity,
               GROUP_CONCAT(DISTINCT source) as sources
        FROM seed_lots
        WHERE source != ''
        GROUP BY species
        ORDER BY species
    """)
    results = []
    for row in rows:
        sources = row["distinct_sources"]
        if sources >= min_sources:
            status = "healthy"
        elif sources >= 2:
            status = "warning"
        else:
            status = "critical"

        # Diversity score: 0-100 based on source count relative to threshold
        score = min(100, round(sources / min_sources * 100))

        results.append({
            **row,
            "diversity_score": score,
            "status": status,
            "min_sources": min_sources,
        })
    return results


@router.get("/alerts")
def diversity_alerts(min_sources: int = Query(3)) -> list[dict]:
    """Return species with fewer than min_sources distinct sources."""
    all_scores = diversity_scores(min_sources)
    return [s for s in all_scores if s["status"] in ("warning", "critical")]


@router.get("/species/{species}")
def species_diversity(species: str) -> dict:
    """Detailed diversity info for a single species."""
    lots = query(
        "SELECT id, name, variety, source, quantity, date_collected FROM seed_lots WHERE species = ? ORDER BY source",
        (species,),
    )
    sources = {}
    for lot in lots:
        src = lot["source"] or "unknown"
        if src not in sources:
            sources[src] = []
        sources[src].append(lot)

    return {
        "species": species,
        "total_lots": len(lots),
        "distinct_sources": len(sources),
        "sources": sources,
    }
