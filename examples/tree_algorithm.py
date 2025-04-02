from collections import OrderedDict

import delphin.codecs.simplemrs
from delphin.mrs import *
import copy



def try_alternative_hole_assignments(all_holes_dict,
                                     node_remaining_holes_list_orig,
                                     node_remaining_floaters_list,
                                     node_assignment_list,
                                     force_hole_floater=None):

    # Grab the first hole to fill and remove it from the list
    if force_hole_floater is not None:
        current_hole = all_holes_dict[node_remaining_holes_list_orig[force_hole_floater[0]]]
        node_remaining_holes_list = copy.deepcopy(node_remaining_holes_list_orig)
        node_remaining_holes_list.pop(force_hole_floater[0])
    else:
        current_hole = all_holes_dict[node_remaining_holes_list_orig[0]]
        node_remaining_holes_list = node_remaining_holes_list_orig[1:]

    # Try each remaining floater in this hole
    for index in range(0, len(node_remaining_floaters_list)):
        if force_hole_floater is not None and index != force_hole_floater[1]:
            continue

        # Grab the current floater and pull from the list for when we recurse
        current_floater = node_remaining_floaters_list[index]
        new_node_remaining_floaters_list = [x for i, x in enumerate(node_remaining_floaters_list) if i != index]

        # Check if constraints are met. If not, prune entire search space by
        # skipping since none of its children can work either
        error_out = []
        if not check_constraints(current_hole["Constraints"], current_floater, error_out):
            continue

        # Hole successfully filled
        # Assign the floater to the hole in a copy of assignments since we will be
        # changing on each loop
        current_assignments = copy.deepcopy(node_assignment_list)
        current_assignments[current_hole["Label"]] = current_floater["Label"]

        if len(new_node_remaining_floaters_list) == 0:
            # We filled the last hole, return the solution
            yield current_assignments
            return

        # If this floater has more holes, add them to a copy of the nodeRemainingHolesListOrig
        # Fixup any of the holes from this floater in a *copy* of holeDict since it also holds the holes
        # and the pointer to the hole is being changed so we don't want other nodes to get changed too
        new_node_remaining_holes_list = copy.deepcopy(node_remaining_holes_list)
        new_hole_dict = copy.deepcopy(all_holes_dict)
        fixup_constraints_for_floater_in_hole(current_hole["Constraints"], current_floater, new_hole_dict)
        for next_hole_name in current_floater["FloaterTreeHoles"]:
            new_node_remaining_holes_list.append(next_hole_name)

        if len(new_node_remaining_holes_list) > 0:
            # recurse
            yield from try_alternative_hole_assignments(new_hole_dict, new_node_remaining_holes_list,
                                                        new_node_remaining_floaters_list,
                                                        current_assignments)

    # At this point we tried all the floaters in this hole
    return


# Check constraints for adding a floater to a hole:
# - Qeq constraints cannot be violated
# - unresolved variables in the floater must be declared in the tree above the hole
def check_constraints(hole_constraints, floater, error_out):
    # A qeq constraint always relates a hole to a (non-hole) handle and says that the handle
    # must be a direct or eventual child in the tree and, if not direct, the only things between
    # the hole and the handle can be quantifiers
    #
    # A qeq constraint of "X qeq Y" says that the direct path from X to Y must only contain quantifiers
    #       - This means that paths that *don't* contain Y can have anything
    #       - The constraint only fails *if* Y appears AND it turns out there was a non-quantifier between X and Y
    #       - Therefore, we have a parameter for each qeq constraint that is true if a non-quantifier was added while it was active
    #
    # So, adding this floater to this hole can fail for two reasons:
    #       1. There are active qeq constraints AND we have already encountered a non-quantifier AND this floater contains the Lo side
    #       2. This floater contains a Lo for which the Hi has not yet been encountered
    #
    # There is theoretically another case: this node contains a Hi but the Lo will never be added because it is elsewhere, but that case
    # will get caught by case 2 above so it is covered

    # Case 1 and 2 only apply if we have unresolved Los in this floater
    for contained_lo in floater["UnresolvedQeqLos"]:
        found_active_qeq = False
        for constraint_lo in hole_constraints["QeqLo"].keys():
            if contained_lo == constraint_lo:
                if hole_constraints["QeqLo"][constraint_lo]:
                    # Case 2: we've already encountered a non-quantifier
                    error_out.append(f"Already encountered non-quantifier for QeqLo: {constraint_lo}")
                    return False
                found_active_qeq = True
                break
        if not found_active_qeq:
            # Case 3: This floater contains a Lo for which the Hi has not yet been encountered
            error_out.append("floater contains a Lo for which the Hi has not yet been encountered: {}".format(contained_lo))
            return False

    # make sure the variables it consumes are declared
    unresolved_variable_count = len(floater["UnresolvedVariables"])
    if unresolved_variable_count > 0:
        intersection = floater["UnresolvedVariables"].intersection(hole_constraints["InScope"])
        if len(intersection) != unresolved_variable_count:
            error_out.append("unresolved variables: {}".format(floater["UnresolvedVariables"] - intersection))
            return False

    return True


# merges constraints from parentHole into holes in the holeList that
# they have keys in the holeNamesToMerge
def fixup_constraints_for_floater_in_hole(parent_hole_constraints_orig, floater, hole_dict):
    # Remove any QEQ constraints from the parentHole that just got satisfied from the floater
    parent_hole_constraints = copy.deepcopy(parent_hole_constraints_orig)
    for unresolved_lo in floater["UnresolvedQeqLos"]:
        if unresolved_lo in parent_hole_constraints_orig["QeqLo"]:
            parent_hole_constraints["QeqLo"].pop(unresolved_lo)

    # merge remaining constraints from the parentHole with all the holes that the floater has
    for target_hole in floater["FloaterTreeHoles"]:
        target_hole_constraints = hole_dict[target_hole]["Constraints"]
        target_hole_constraints["QeqLo"].update(parent_hole_constraints["QeqLo"])
        target_hole_constraints["InScope"] |= parent_hole_constraints["InScope"]

    return


# Propagate information about the whole floater tree to the top node and to the holes it contains:
#     - For every hole it contains:
#         - fill the "Constraints" key with scope and QEQ constraints
#           that propagate to it from the top of this tree down.
#     - For the top_node_of_floater:
#         - fill in the "UnresolvedVariables" set with all the variables that are consumed anywhere
#           in this tree but not declared in it
#         - fill in the "UnresolvedQeqLos" set with the list of qeq lo handles that are not satisfied in the tree
#             - We know that, within the tree, these cannot have non-quantifiers above them because
#               then the tree would NEVER work (TODO: we should assert this)
#         - gather all holes in "FloaterTreeHoles" that are in all children and put in the top node so we don't have to search for them later
#
# Constraints:
# {
#     "QeqLo" : { "LoHandle" : True or False if there has been a non-quantifier since the hi handle was added },
#     "InScope" : Set(variables in scope) # Variables that are declared by quantifiers above this hole in the tree
# }
def initialize_floater_data(hole_dict, top_node_of_floater, current_tree, global_qeqs, current_constraints):
    if current_constraints is None:
        # This is the initial call and represents the top node
        current_constraints = {"QeqLo": {}, "InScope": set()}
        top_node_of_floater["UnresolvedVariables"] = set()
        top_node_of_floater["UnresolvedQeqLos"] = set()
        top_node_of_floater["FloaterTreeHoles"] = OrderedDict()

    current_tree_label = current_tree["Label"]

    # Copy the constraints since they will change as they propagate down each branch
    # of the tree
    new_constraints = copy.deepcopy(current_constraints)

    # If this node consumes variables that aren't in scope, they are unresolved
    # add to the top node
    top_node_of_floater["UnresolvedVariables"] = top_node_of_floater["UnresolvedVariables"].union(
        current_tree["ConsumedVariables"].difference(new_constraints["InScope"]))

    # See if QEQs get turned off for this node. Qeqs always relate a "hole qeq node"
    # So we only have to check with turning them off
    if current_tree_label in new_constraints["QeqLo"]:
        new_constraints["QeqLo"].pop(current_tree_label)
    elif current_tree["QeqLo"]:
        # this was a Lo that didn't have a Hi above it, put it in the UnresolvedQeqLos
        top_node_of_floater["UnresolvedQeqLos"].add(current_tree_label)

    # If this node declares a variable, add it to the in-scope list for children
    variable = current_tree["Variable"]
    if variable is not None:
        new_constraints["InScope"].add(variable)
    else:
        # This is not a quantifier, therefore there should not be any active Qeqs
        # or else the grammar is generating invalid trees
        assert len(new_constraints["QeqLo"]) == 0, f"There are active constraints that get violated in a floater {current_tree}"

    # Fill any holes this node has with new_constraints and fill in the top node with all holes
    # from children
    for hole in current_tree["Holes"]:
        assert hole in hole_dict, "{} should be in holelist".format(hole)
        assert hole_dict[hole]["Constraints"] is None, f"{hole} constraints should only be set once since the hole should only exist in one place"

        # Collect this hole in the top node
        top_node_of_floater["FloaterTreeHoles"][hole] = hole

        # Hole constraints get modified as the tree gets built up later, so make a copy so all are independent
        newHoleConstraints = copy.deepcopy(new_constraints)

        # See if this hole is the Hi for any QEQs
        for qeq in global_qeqs:
            if qeq["Hi"] == hole:
                newHoleConstraints["QeqLo"][qeq["Lo"]] = False

        hole_dict[hole]["Constraints"] = newHoleConstraints

    # Recurse through arguments gathering data
    for childNode in current_tree["Args"]:
        initialize_floater_data(hole_dict, top_node_of_floater, childNode, global_qeqs, new_constraints)


# Converts a list of predications into an initial forest of trees of FloaterNodes
#
# Builds up the initial tree structure for floaters by assigning any predications with handles to
# predicates that use those handles as arguments (i.e. arguments that are not holes).
#
# Does this by creating a new JSON structure using CreateFloaterNode(). This is what is returned and used.
#
# When returned, each FloaterNode structure in the tree has been initialized with data that can be determined
# from looking at the node itself.  Any data that is determined by looking at the whole floater tree
# (like constraints), is filled in by InitializeFloaterData
#
# The algorithm depends on the fact that there are no loops, so once you've attached
# all possible children you are done:
#     - Start with a list of predicates
#     - remove the first one
#     - see if any of the remaining are its children, remove them from the list and attach to it
#     - add the first one back into the list
#     - go to the next one
#     - By the time you are finished, each node will have its children added and will have built all the trees you can build
#     - If you get to the end of the list and you may have more than one tree, which will be invalid for a solved MRS so this isn't a solution
#
# returns: hole_dict, floater_dict (a dictionary of FloaterNodes indexed by the top Label and a dictionary of holes indexed by its Label)
def get_holes_and_floaters(predications, global_qeqs):
    holes_dict = {}

    # Create a dict that maps predication labels to predications
    # multiple predications can have the same label, so we need to map each label a list
    # also need to keep track of which predications have already been turned into trees
    # so the structure looks like this:
    # { "Label": { "Predication":[] "Tree": None } }
    predication_by_label = {}
    for predication in predications:
        # Top is a fake predicate just to make logic easier, and always has a "hole" to
        # allow anything to be the top of the tree, remove it from the list of floaters but
        # keep it as a hole
        if predication.predicate == "TOP":
            holes_dict[predication.args["ARG0"]] = create_hole_node(predication.args["ARG0"])
        else:
            if predication.label not in predication_by_label:
                predication_by_label[predication.label] = {"Predication": [], "Tree": None}

            predication_by_label[predication.label]["Predication"] += [predication]

    while True:
        # pick the next item off the open list that doesn't yet have a tree
        # We are looping through predication_by_label by keys() which is an arbitrary order
        # So we need to sort them so the order doesn't change as things are removed
        sorted_labels = sorted(predication_by_label.keys())
        index = 0
        while index < len(sorted_labels):
            predication_item = predication_by_label[sorted_labels[index]]
            if predication_item["Tree"] is None:
                break
            index += 1

        if index == len(sorted_labels):
            # We've built all possible trees
            # There must always be the same number of holes as initial trees
            if len(holes_dict) != len(sorted_labels):
                # This happens sometimes even though it isn't supposed to be valid
                # so we shouldn't assert, but it also isn't valid
                print("GRAMMAR ERROR: Holes = {} and Floaters = {}".format(len(holes_dict), len(sorted_labels)))
                return None, None

            # Just return the FloaterNode tree, not the actual predications
            floater_dict = {}
            for label in sorted_labels:
                floater_dict[label] = predication_by_label[label]["Tree"]

            return holes_dict, floater_dict

        # Create a dict of predications without this item in it
        remaining_labels = sorted_labels[0:index] + sorted_labels[index + 1:]
        potential_child_dict = {}
        for label in remaining_labels:
            potential_child_dict[label] = predication_by_label[label]

        # Build whatever tree we can with this as the top
        predication_item["Tree"] = build_initial_tree_from_predication_item(global_qeqs, predication_item,
                                                                            potential_child_dict, holes_dict)

        # Add it back into the potential_child_dict dict it in case it is part of an
        # even larger initial tree
        potential_child_dict[predication_item["Tree"]["Label"]] = predication_item

        # Use this one on the next loop
        predication_by_label = potential_child_dict



# Builds the initial tree for one or more predications that share the same handle
# i.e. that are in conjunction
def build_initial_tree_from_predication_item(global_qeqs, predication_item, remaining_predications_by_label, holes_dict):
    conjunction_nodes = []
    for predication in predication_item["Predication"]:
        conjunction_nodes.append(build_initial_tree(global_qeqs, predication,
                                                    remaining_predications_by_label, holes_dict))

    if len(conjunction_nodes) == 1:
        return conjunction_nodes[0]
    else:
        # Note that predicationItem might have multiple predicates with the same handle
        # in its predicationItem["Predication"] list.  Handle this by building a fake node
        # with the handle they share, and putting them as children
        # Since it is a fake node, the only data that needs to be filled in for the FloaterNode
        # is QeqLo since there are no variables or holes in it
        # Because Qeqs are done by label, these must all have the same value by definition so just
        # use the first one
        return create_floater_node(conjunction_nodes[0]["Label"], None, set(), conjunction_nodes,
                                   [], conjunction_nodes[0]["QeqLo"])


# Creates an initial tree by looking at the args of predication and, if they are handles to real labels
# (and not holes), adding them as children then removing them from remainingPredicationsByLabel
# - Creates and returns a "Floater Node" json from data in the predication using CreateFloaterNode()
# - Does the same for any nodes that get added to the tree (if they don't already have one)
# - Also fills in holesDict with any holes it finds in the predication or any nodes that get added as children
#
# The FloaterNode json needs to have tree-wide information initialized still, this is done by InitializeFloaterData
#
# returns a FloaterNode json that represents the root of the tree that was built
def build_initial_tree(global_qeqs, predication, remaining_predications_by_label, holes_dict):
    is_quantifier = "RSTR" in predication.args.keys()
    arg_nodes = []
    variable = None
    consumed_variables = set()
    holes = []
    is_qeq_lo = False

    # Go through the args in the predication and see if there are labels
    # that have the same value
    for arg_name in predication.args.keys():
        # Skip ARG0 for quantifiers since it *defines* the variable
        # and doesn't use it
        if is_quantifier and arg_name == "ARG0":
            variable = predication.args[arg_name]
            continue

        # CARGs contain constants not labels or variables
        if arg_name != "CARG":
            value = predication.args[arg_name]
            if value[0] == "x":
                consumed_variables.add(value)
            elif value[0] == "h":
                # Found an 'h' argument, see if there are labels using this same value
                if value in remaining_predications_by_label:
                    # This is a real label, get and remove its predication from the remaining list
                    arg_predication = remaining_predications_by_label.pop(value)
                    # if it already has a tree, just attach it and continue
                    if arg_predication["Tree"] is not None:
                        arg_nodes.append(arg_predication["Tree"])
                    else:
                        # add it and recurse
                        arg_nodes.append(build_initial_tree_from_predication_item(global_qeqs, arg_predication,
                                                                                  remaining_predications_by_label, holes_dict))
                else:
                    # This argument is a hole, add it to the dictionary
                    holes_dict[value] = create_hole_node(value)

                    # And to the list of holes for this node
                    holes.append(value)
            else:
                # non-x variable of some type, skip
                continue

    # Remember if this node is the Lo part of a Qeq
    label = predication.label
    for item in global_qeqs:
        if item["Lo"] == label:
            is_qeq_lo = True
            break

    return create_floater_node(label, variable, consumed_variables, arg_nodes, holes, is_qeq_lo)


# hole node:
# {
#     "h1" : { "Label": "h1", etc,         # Label assigned to this hole
#              "Constraints": Constraints, # Set of constraints propagated to this hole
#              "Floater": Value            # (used later) current floater assigned to the hole }
# }
def create_hole_node(label, constraints=None, floater=None):
    return {"Label": label, "Constraints": constraints, "Floater": floater}


# Floater Node:
# {
#     # These items represent data that is only about the predication that this node represents:
#     "Label"             : "h1",
#     "Variable"          : "x12",        # If this node is a quantifier, this is the variable it defines, Otherwise None
#     "ConsumedVariables" : set() # The variables that this node consumes
#     "Args"              : [ChildNode, ChildNode...] # ChildNodes that are holes have empty args
#     "Holes"             : [] # List of Holes that it contains like "h1", etc
#     "QeqLo"             : True/False # True if this label is a qeq Lo
#
#     # These are only for floater nodes that are the top of a finished floater tree
#     # and represent information about the whole tree.  They must get updated and the tree gets
#     # updated as we solve
#     "UnresolvedQeqLos"   : set("h0") # list of qeq low handles that are not satisfied in the tree (including this node), meaning the Hi and Lo nodes aren't in the tree itself
#     "UnresolvedVariables": set("x0") # Added later only to nodes which are the top of floaters
#     "InitialTreeHoles"   : set("h0") # Added later to consolidate all holes in the initial tree
# }
def create_floater_node(label, variable, consumed_variables, arg_nodes, holes, is_qeq_lo):
    return {"Label": label,
            "Variable": variable,
            "ConsumedVariables": consumed_variables,
            "Args": arg_nodes,
            "Holes": holes,
            "QeqLo": is_qeq_lo}


class TooComplicatedError(ValueError):
    def __init__(self, arg):
        self.strerror = arg
        self.args = {arg}


# Returns a list of X variables that have no quantifier
# which can happen (e.g. Yell "I am Free")
def find_unquantified_x_variables(mrs):
    no_quantifier = set()
    vars = [x for x in mrs.variables.keys() if x[0] == "x"]
    for current_var in vars:
        found = False
        for predication in mrs.predications:
            if predication.is_quantifier():
                if predication.args["ARG0"] == current_var:
                    found = True
                    break
        if not found:
            no_quantifier.add(current_var)

    return no_quantifier


# Figure out which predication labels are unused in any argument. i.e. "floating".
# Those need to be assigned to holes. Also figure out which Label references are not defined as the Label of an EP, those are the holes
#
# Is generator that returns a solution dictionary of all different sets of key = hole and value = predication handles that fill
# it each time it is iterated
#
# For phrases that are wh-questions, the root predication needs to be which_q, and setting required_root_label to the MRS label for the
# which_q predication ensures this
def valid_hole_assignments(mrs, max_holes, required_root_label, raw_mrs=""):
    # Add the "top" Label as an ARG0 to an unused MRS predication, which makes it a hole,
    # just to make the logic simpler since we will later map floaters to holes and want to have
    # a way to indicate that any floater could be the "top"
    all_predications = copy.deepcopy(mrs.predications)
    all_predications.append(EP("TOP", "h0", {"ARG0": mrs.top}))

    # Get the Hole and Floater data
    global_qeqs = []
    for constraint in mrs.hcons:
        assert constraint.relation == "qeq", f"Don't know relation {constraint.relation}"
        global_qeqs.append({"Hi": constraint.hi, "Lo": constraint.lo})

    hole_dict, floater_dict = get_holes_and_floaters(all_predications, global_qeqs)
    if hole_dict is None:
        return None

    if max_holes is not None and len(hole_dict) > max_holes:
        # This is just to abort processing a tree that will take too long
        raise TooComplicatedError(f"Too many holes: {len(hole_dict)}")

    # Then propagate constraints to each hole in each floater
    for floater_tree_key in floater_dict.keys():
        floater = floater_dict[floater_tree_key]
        initialize_floater_data(hole_dict, floater, floater, global_qeqs, None)

    # And constraints and InScope to the top hole
    hole_dict["h0"]["Constraints"] = {"QeqLo": {}, "InScope": set()}

    # See if new QEQs get turned on for this node
    for qeq in global_qeqs:
        if qeq["Hi"] == "h0":
            hole_dict["h0"]["Constraints"]["QeqLo"][qeq["Lo"]] = False

    # There are cases in the grammar (e.g. "yell 'I am free'") where x variables
    # are used but not put in scope by a quantifier and the grammar is supposedly valid
    # enable these cases by putting those variables in scope for the top
    hole_dict["h0"]["Constraints"]["InScope"] = find_unquantified_x_variables(mrs)

    # TryAlternativeHoleAssignments requires a floater list, not a dict
    floater_list = list(floater_dict.values())

    # Finally return each valid set of assignments
    force_hole_floater = None
    if required_root_label is not None:
        for floater_index in range(len(floater_list)):
            if floater_list[floater_index]["Label"] == required_root_label:
                force_hole_floater = [0, floater_index]
                break

    for assignment in try_alternative_hole_assignments(hole_dict, [mrs.top],
                                                       floater_list, {},
                                                       force_hole_floater=force_hole_floater):
        yield mrs, assignment
        

