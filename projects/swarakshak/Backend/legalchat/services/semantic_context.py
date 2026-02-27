# legalchat/services/semantic_context.py

from typing import Dict, List


class SemanticContextBuilder:
    """
    Builds safe semantic context for retrieval.
    This context is used ONLY to enrich the legal query,
    NOT to influence verdict logic.
    """

    def __init__(self):
        pass

    def build(
        self,
        rewritten_legal_query: str,
        session_context: List[Dict]
    ) -> Dict:
        """
        rewritten_legal_query:
            Output of rewrite_query.py (LLM, legal terms)

        session_context:
            Output of SessionMemory.get_context()

        Returns:
            {
              "enrichment_text": str,
              "context_metadata": dict,
              "locked_domain": str (optional)
            }
        """

        if not session_context:
            return {
                "enrichment_text": rewritten_legal_query,
                "context_metadata": {},
                "locked_domain": None
            }

        # IMPLEMENTATION REQUIREMENT 1: Semantic Topic Lock
        # "After the first successful retrieval, store primary_legal_topic..."
        # We assume the first turn in history is the "anchor" or "lock".
        locked_turn = session_context[0]
        locked_domain = locked_turn.get("legal_domain")
        
        # Collect all context, but prioritize locked turn for injection
        domains = set()
        acts = set()
        sections = set()
        doctrines = set()

        for turn in session_context:
            if "legal_domain" in turn and turn["legal_domain"]:
                domains.add(turn["legal_domain"])

            if "statute_names" in turn and isinstance(turn["statute_names"], list):
                for act in turn["statute_names"]:
                    acts.add(act)

            if "section_numbers" in turn and isinstance(turn["section_numbers"], list):
                for sec in turn["section_numbers"]:
                    sections.add(str(sec))
            
            if "primary_doctrine" in turn and turn["primary_doctrine"]:
                doctrines.add(turn["primary_doctrine"])

        # Build enrichment string (retrieval-safe)
        enrichment_parts = []

        # 1. Inject Domain Keywords (Crucial for classify_domain)
        # CLEAN ENRICHMENT RULE: Remove generic words.
        # Use minimal keywords to trigger domain detection without noise.
        DOMAIN_KEYWORDS = {
            "contract_clause": "contract",
            "contract_law": "contract law",
            "employment_contract": "employment",
            "labour_law": "labour industrial",
            "criminal_confusion": "criminal",
            "foreign_jurisdiction": "foreign"
        }
        
        if locked_domain and locked_domain in DOMAIN_KEYWORDS:
             enrichment_parts.append(DOMAIN_KEYWORDS[locked_domain])

        if acts:
            # Include statute name (once)
            # Use the first/most frequent statute if multiple, but typically locked to one family
            # For safety, just take the first one found in the set to avoid duplication
            enrichment_parts.append(next(iter(acts)))

        # if domains:
        #    enrichment_parts.append(" ".join(domains))

        if sections:
            # Max 1-2 section numbers, deduplicated
            sorted_secs = sorted(list(sections))
            top_secs = sorted_secs[:2]
            enrichment_parts.append(
                "Section " + " Section ".join(top_secs)
            )
        
        if doctrines:
            # Doctrine keyword if available
            enrichment_parts.append(" ".join(doctrines))

        enrichment_text = " ".join(enrichment_parts)

        # We return the enrichment text separately now
        return {
            "enrichment_text": enrichment_text,
            "context_metadata": {
                "domains": list(domains),
                "acts": list(acts),
                "sections": list(sections),
                "doctrines": list(doctrines)
            },
            "locked_domain": locked_domain
        }
