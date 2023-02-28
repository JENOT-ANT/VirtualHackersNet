ERRORS: dict = {
    0: "incorrect amount of arguments",
    1: "incorrect values of arguments",
    2: "too high exploit level",
    3: "max amount of exploits reached",
    4: "purchase failed",
    5: "failed to add the offer",
    6: "you are not registered yet",
    7: "failed to join to the squad",
}

EXPLANATIONS: dict = {
    0: "take a look at 'help' cmd here",
    1: "take a look at '> help' cmd here",
    2: "exploit lvl shouldn't be grather than your AI lvl",
    3: "max lvl reached",
    4: "max amount of exploits reached",
    5: "transaction failed",
    6: "no exploit with that id",
    7: "max amount of members reached",
}


def error(error_id: int, explanation_id: int=None) -> str:
    if explanation_id == None:
        return f"{ERRORS[error_id].capitalize()}!"
    
    return f"{ERRORS[error_id].capitalize()}! {EXPLANATIONS[explanation_id].capitalize()}."
