from .models import Restriction


def active_for(person):
    return list(Restriction.objects.filter(person=person, lifted_at__isnull=True).select_related("species"))


def check(person, species=None):
    """Whether the person may adopt. With a species, only restrictions that apply to it block."""
    active = active_for(person) if person else []
    blocking = [r for r in active if species is None or r.applies_to(species)]
    return {
        "can_adopt": not blocking,
        "restrictions": [
            {
                "id": r.id,
                "reason": r.get_reason_display(),
                "species": r.species.plural_name if r.species else "Todas las especies",
                "notes": r.notes,
                "created_at": r.created_at,
                "blocks_this_animal": r in blocking,
            }
            for r in active
        ],
    }
