from __future__ import annotations

import re
from dataclasses import dataclass


STRONG_TERMS = {
    "because",
    "evidence",
    "data",
    "therefore",
    "example",
    "shows",
    "impact",
    "clear",
    "direct",
}

EMOTIONAL_TERMS = {
    "compassion",
    "suffering",
    "harm",
    "victims",
    "children",
    "families",
    "empathy",
    "cruel",
    "justice",
    "fear",
    "safety",
    "rights",
    "freedom",
    "dignity",
}

CONTROVERSIAL_TERMS = {
    "censorship",
    "abortion",
    "death",
    "war",
    "racism",
    "police",
    "religion",
    "guns",
    "immigration",
    "genocide",
    "authoritarian",
    "surveillance",
    "propaganda",
    "discrimination",
}

AMPLIFIER_PHRASES = {
    "people are dying",
    "this is cruel",
    "basic human rights",
    "real harm",
    "directly harms",
    "morally indefensible",
    "human cost",
}

TOXIC_TERMS = {
    "abort till",
    "abort until",
    "if a child is a girl",
    "if the baby is a girl",
    "female babies",
    "female baby",
    "male babies",
    "male baby",
    "until a boy is born",
    "until a son is born",
    "because she is a girl",
    "because it's a girl",
    "because the baby is a girl",
    "gender selection",
    "selective abortion",
    "eugenic",
    "eugenics",
    "inferior",
    "undesirable",
}

PROTECTED_GROUP_TERMS = {
    "girl",
    "boy",
    "female",
    "male",
    "race",
    "racial",
    "ethnicity",
    "ethnic",
    "religion",
    "religious",
    "muslim",
    "christian",
    "jewish",
    "hindu",
    "black",
    "white",
    "asian",
    "latino",
    "arab",
    "african",
    "indian",
    "mexican",
    "chinese",
    "japanese",
    "immigrant",
    "migrant",
    "refugee",
    "gay",
    "lesbian",
    "trans",
    "transgender",
    "queer",
    "bisexual",
    "nonbinary",
    "woman",
    "women",
    "man",
    "men",
    "gender",
    "ethnicity",
    "ethnic group",
    "disabled",
    "disability",
    "autistic",
    "down syndrome",
    "genetic purity",
    "poor",
    "poverty",
    "low income",
    "working class",
    "homeless",
    "uneducated",
    "lower class",
}

SELECTION_VERBS = {
    "abort",
    "keep",
    "only",
    "select",
    "choose",
    "replace",
    "prefer",
    "discard",
    "eliminate",
}

EXCLUSION_PHRASES = {
    "keep only",
    "only male",
    "only female",
    "prefer male",
    "prefer female",
    "not people like",
    "get rid of",
    "filter out",
    "weed out",
    "screen out",
    "exclude them",
    "remove them",
    "keep our kind",
    "no girl child",
    "no boy child",
    "no female child",
    "no male child",
    "no girls",
    "no boys",
    "not welcome",
    "don't belong",
    "do not belong",
    "should be excluded",
    "should be removed",
    "should not exist here",
    "keep them out",
    "leave them out",
    "push them out",
    "not one of us",
}

DISCRIMINATORY_ACTION_TERMS = {
    "exclude",
    "segregate",
    "ban",
    "remove",
    "eliminate",
    "sterilize",
    "deport",
    "replace",
    "purify",
    "cleanse",
    "screen out",
    "weed out",
    "filter out",
    "get rid of",
    "deny housing",
    "deny jobs",
    "deny service",
    "block from school",
    "block from work",
    "refuse entry",
    "refuse service",
}

DEHUMANIZING_TERMS = {
    "inferior",
    "lesser",
    "undesirable",
    "not fit",
    "subhuman",
    "unclean",
    "vermin",
    "breeding stock",
    "burden on society",
    "should not exist",
}

DISCRIMINATORY_JUSTIFICATION_TERMS = {
    "because they are",
    "for being",
    "due to their race",
    "due to their sex",
    "due to disability",
    "because of religion",
    "because of gender",
    "genetic quality",
    "keep society pure",
    "make sure no",
    "ensure no",
    "because they are poor",
    "because they are women",
    "because they are men",
    "because they are muslim",
    "because they are christian",
    "because they are jewish",
    "because they are immigrants",
    "because of ethnicity",
    "because of class",
    "because of income",
}

EXISTENCE_DENIAL_PATTERNS = {
    "no {group} is born",
    "no {group} are born",
    "no {group} should be born",
    "{group} should not be born",
    "prevent {group} from being born",
    "make sure no {group} is born",
    "ensure no {group} is born",
    "so that no {group} is born",
}

GENERAL_EXCLUSION_PATTERNS = {
    "no {group}",
    "not {group}",
    "without {group}",
    "exclude {group}",
    "ban {group}",
    "remove {group}",
    "deport {group}",
    "segregate {group}",
    "keep out {group}",
    "filter out {group}",
    "screen out {group}",
    "get rid of {group}",
    "no place for {group}",
    "{group} are not welcome",
    "{group} do not belong",
    "{group} should be excluded",
    "{group} should be removed",
}

POSITIVE_STANCE_TERMS = {
    "yes",
    "pro",
    "for",
    "support",
    "supports",
    "agree",
    "in favor",
    "should",
    "must",
    "necessary",
    "beneficial",
    "worth it",
}

NEGATIVE_STANCE_TERMS = {
    "no",
    "con",
    "against",
    "oppose",
    "opposes",
    "disagree",
    "should not",
    "must not",
    "unnecessary",
    "harmful",
    "dangerous",
    "reject",
}

POSITIVE_ARGUMENT_TERMS = {
    "should",
    "must",
    "need",
    "necessary",
    "benefit",
    "protect",
    "helps",
    "improves",
    "better",
    "worth",
    "supports",
}

NEGATIVE_ARGUMENT_TERMS = {
    "should not",
    "must not",
    "dangerous",
    "worse",
    "reject",
    "oppose",
    "against",
    "unnecessary",
    "fails",
    "too risky",
    "goes too far",
    "not beneficial",
    "not predictable",
    "unpredictable",
    "unstable",
    "not practical",
    "impractical",
    "not workable",
    "won't work",
    "will not work",
    "ineffective",
    "harmful",
    "creates problems",
    "causes problems",
    "bad idea",
    "not a good idea",
    "not viable",
    "not sustainable",
    "not realistic",
}


@dataclass
class CrowdSignal:
    weighted_terms: int
    emotional_hits: int
    controversial_hits: int
    amplifier_bonus: int
    contrast_bonus: int
    emphasis_bonus: int
    crowd_backlash: bool
    descriptors: list[str]


def analyze_crowd_signal(text: str) -> CrowdSignal:
    normalized_text = text.lower()
    words = re.findall(r"\w+", normalized_text)
    weighted_terms = sum(1 for word in words if word in STRONG_TERMS)
    emotional_hits = sum(1 for word in words if word in EMOTIONAL_TERMS)
    controversial_hits = sum(1 for word in words if word in CONTROVERSIAL_TERMS)
    toxic_hits = sum(1 for phrase in TOXIC_TERMS if phrase in normalized_text)
    protected_group_hits = sum(1 for phrase in PROTECTED_GROUP_TERMS if phrase in normalized_text)
    selection_hits = sum(1 for phrase in SELECTION_VERBS if phrase in normalized_text)
    exclusion_hits = sum(1 for phrase in EXCLUSION_PHRASES if phrase in normalized_text)
    discriminatory_action_hits = sum(
        1 for phrase in DISCRIMINATORY_ACTION_TERMS if phrase in normalized_text
    )
    dehumanizing_hits = sum(1 for phrase in DEHUMANIZING_TERMS if phrase in normalized_text)
    discriminatory_justification_hits = sum(
        1 for phrase in DISCRIMINATORY_JUSTIFICATION_TERMS if phrase in normalized_text
    )
    existence_denial_hits = sum(
        1
        for group in PROTECTED_GROUP_TERMS
        for pattern in EXISTENCE_DENIAL_PATTERNS
        if pattern.format(group=group) in normalized_text
    )
    general_exclusion_hits = sum(
        1
        for group in PROTECTED_GROUP_TERMS
        for pattern in GENERAL_EXCLUSION_PATTERNS
        if pattern.format(group=group) in normalized_text
    )
    amplifier_bonus = sum(1 for phrase in AMPLIFIER_PHRASES if phrase in normalized_text)
    contrast_bonus = 3 if any(token in words for token in {"but", "yet", "however"}) else 0
    emphasis_bonus = 2 if len(words) >= 12 and any(token in words for token in {"must", "cannot", "never"}) else 0

    crowd_backlash = (
        toxic_hits > 0
        or (protected_group_hits >= 1 and selection_hits >= 1)
        or (protected_group_hits >= 1 and exclusion_hits >= 1)
        or (protected_group_hits >= 1 and discriminatory_action_hits >= 1)
        or (protected_group_hits >= 1 and dehumanizing_hits >= 1)
        or (protected_group_hits >= 1 and discriminatory_justification_hits >= 1)
        or existence_denial_hits >= 1
        or general_exclusion_hits >= 1
        or dehumanizing_hits >= 2
    )

    descriptors: list[str] = []
    if emotional_hits:
        descriptors.append("compassion-driven")
    if controversial_hits:
        descriptors.append("controversial")
    if weighted_terms >= 2:
        descriptors.append("well-structured")
    if crowd_backlash:
        descriptors.append("ethically toxic")

    return CrowdSignal(
        weighted_terms=weighted_terms,
        emotional_hits=emotional_hits,
        controversial_hits=controversial_hits,
        amplifier_bonus=amplifier_bonus,
        contrast_bonus=contrast_bonus,
        emphasis_bonus=emphasis_bonus,
        crowd_backlash=crowd_backlash,
        descriptors=descriptors,
    )


def stance_consistency(stance: str, text: str) -> int:
    normalized_stance = stance.lower().strip()
    normalized_text = text.lower()
    stance_orientation = _orientation_from_text(
        normalized_stance,
        POSITIVE_STANCE_TERMS,
        NEGATIVE_STANCE_TERMS,
    )
    argument_orientation = _orientation_from_text(
        normalized_text,
        POSITIVE_ARGUMENT_TERMS,
        NEGATIVE_ARGUMENT_TERMS,
    )
    if stance_orientation == 0 or argument_orientation == 0:
        return 0
    return 1 if stance_orientation == argument_orientation else -1


def _orientation_from_text(text: str, positive_terms: set[str], negative_terms: set[str]) -> int:
    positive_hits = sum(1 for term in positive_terms if term in text)
    negative_hits = sum(1 for term in negative_terms if term in text)
    if positive_hits == negative_hits:
        return 0
    return 1 if positive_hits > negative_hits else -1
