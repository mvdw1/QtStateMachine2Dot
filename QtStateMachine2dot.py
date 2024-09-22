import re
import argparse
import os
from graphviz import Digraph

class Diagram:
    DEBUG = True
    def __init__(self):
        self.states = set()
        self.transitions = []

    def addStates(self, states):
        for state in states:
            self.addState(state)

    def addTransitions(self, transitions):
        for transition in transitions:
            self.addTransition(*transition)
    
    def addState(self, state):
        self.states.add(state)

    def addTransition(self, fromState, toState, label=None, group=None):
        if fromState in self.states and toState in self.states:
            self.transitions.append((fromState, toState, label, group))
        else:
            if self.DEBUG:
                print(f"Both states {fromState}, {toState} must be added to the diagram before adding a transition.")
        
                return
            raise ValueError(f"Both states {fromState}, {toState} must be added to the diagram before adding a transition.")
        
    def setGroupColor(self, group, color):
        if not hasattr(self, 'groupColors'):
            self.groupColors = {}
        self.groupColors[group] = color

    def __str__(self):
        result = "States:\n"
        for state in self.states:
            result += f"  {state}\n"
        result += "Transitions:\n"
        for fromState, toState, label, group in self.transitions:
            result += f"  {fromState} -> {toState}"
            if label:
                result += f" [label={label}]"
            if group:
                result += f" [group={group}]"   
            result += "\n"
        return result
    
    def toDot(self, filename, verbose=False, visualize=False):
        dot = Digraph(comment='State Machine')
        for state in self.states:
            dot.node(state, shape='circle')
        for fromState, toState, label, group in self.transitions:
            attributes = {}
            if label:
                attributes['label'] = label
            if group and hasattr(self, 'groupColors') and group in self.groupColors:
                attributes['color'] = self.groupColors[group]
            dot.edge(fromState, toState, **attributes)
        
        if filename:
            dot.render(filename, format='png')
            if verbose:
                print(f"DOT file written to {filename}.png")
        if visualize:
            dot.view()
            print(f"DOT file written to {filename}")

class QtStateMachineParser:
    def __init__(self, filename):
        self.filename = filename
        self.stateMachines = {}
        
    def findStateMachines(self, code):
        # Regular expressions to match state machine declarations
        stateMachinePatterns = [
            re.compile(r'(\w+)\s*=\s*new\s*QStateMachine'),  # Matches: machine = new QStateMachine
            re.compile(r'QStateMachine\s+(\w+);'),           # Matches: QStateMachine machine;
            re.compile(r'QStateMachine\s*\*\s*(\w+)\s*=\s*new\s*QStateMachine'),  # Matches: QStateMachine* machine = new QStateMachine
            re.compile(r'std::unique_ptr<QStateMachine>\s+(\w+)\s*=\s*std::make_unique<QStateMachine>\(\)'),  # Matches: std::unique_ptr<QStateMachine> machine = std::make_unique<QStateMachine>();
            re.compile(r'std::shared_ptr<QStateMachine>\s+(\w+)\s*=\s*std::make_shared<QStateMachine>\(\)')   # Matches: std::shared_ptr<QStateMachine> machine = std::make_shared<QStateMachine>();
        ]# TODO: extend with more patterns if needed

        stateMachines = []
        for pattern in stateMachinePatterns:
            stateMachines.extend(pattern.findall(code))
        return stateMachines
    
    def findTransitions(self, code):
        transitionPatterns = [
            re.compile(r'(\w+)(\.|->)addTransition\(([^,]+),\s*&(\w+)::(\w+),\s*(\w+)\);'),  # Matches: state->addTransition(sender, &SenderClass::signal, targetState);
            re.compile(r'(\w+)(\.|->)addTransition\(([^,]+),\s*SIGNAL\((\w+)\(\)\),\s*(\w+)\);'),  # Matches: state->addTransition(sender, SIGNAL(signal()), targetState);
            re.compile(r'(\w+)(\.|->)addTransition\(([^,]+),\s*\[\w*\]\s*\{[^}]*\},\s*(\w+)\);'),  # Matches: state->addTransition(sender, &SenderClass::signal, [targetState] { ... });
            re.compile(r'QSignalTransition\s*\*\s*(\w+)\s*=\s*new\s*QSignalTransition\(([^,]+),\s*SIGNAL\((\w+)\(\)\)\);\s*\1->setTargetState\((\w+)\);\s*\w+->addTransition\(\1\);')  # Matches: QSignalTransition* transition = new QSignalTransition(sender, SIGNAL(signal())); transition->setTargetState(targetState); state->addTransition(transition);
        ]
        transitions = []
        for pattern in transitionPatterns:
            transitions.extend(pattern.findall(code))
        return transitions
    
    
    
    
    def parse(self):
        with open(self.filename, 'r') as file:
            code = file.read()

        # Regular expressions to match Qt state machine constructs
        propertyPattern = re.compile(r'(\w+)->assignProperty\((\w+),\s*"(\w+)",\s*(\w+)\);')
        connectPattern = re.compile(r'connect\((\w+),\s*&(\w+)::(\w+),\s*(\w+),\s*&(\w+)::(\w+)\);')
        statePattern = re.compile(r'(\w+)(\.|->)addState\((\w+)\);')
        initialStatePattern = re.compile(r'(\w+)->setInitialState\((\w+)\);')
        startPattern = re.compile(r'(\w+)->start\(\);')

        # Find all matches
        #stateMachines = stateMachinePattern.findall(code)
        stateMachines = self.findStateMachines(code)
        transitions = self.findTransitions(code)
        properties = propertyPattern.findall(code)
        connections = connectPattern.findall(code)
        states = statePattern.findall(code)
        initialStates = initialStatePattern.findall(code)
        starts = startPattern.findall(code)

        # Initialize state machines
        for sm in stateMachines:
            self.stateMachines[sm] = {
                'states': [],
                'transitions': [],
                'properties': [],
                'connections': [],
                'initialStates': [],
                'starts': []
            }

        # Associate states with state machines
        for match in states:
            stateMachine = match[0]
            if stateMachine in self.stateMachines:
                self.stateMachines[stateMachine]['states'].append((match[2]))
        
        # Associate transitions with state machines
        for match in transitions:
            # check per machine whether the target / source state are present for that machine
            for machine in stateMachines:
                if(match[0] in self.stateMachines[machine]['states'] and match[5] in self.stateMachines[machine]['states']):
                    self.stateMachines[machine]['transitions'].append((match[0], match[5], match[3]))
 

        # Associate properties with state machines
        # for match in properties:
        #     stateMachine = match[0]
        #     if stateMachine in self.stateMachines:
        #         self.stateMachines[stateMachine]['properties'].append((match[0], match[2], match[3]))

        # Associate connections with state machines
        # for match in connections:
        #     stateMachine = match[0]
        #     if stateMachine in self.stateMachines:
        #         self.stateMachines[stateMachine]['connections'].append((match[0], match[2], match[3], match[5]))



        # Associate initial states with state machines
        # for match in initialStates:
        #     stateMachine = match[0]
        #     if stateMachine in self.stateMachines:
        #         self.stateMachines[stateMachine]['initialStates'].append((match[1]))

        # Associate starts with state machines
        # for match in starts:
        #     stateMachine = match[0]
        #     if stateMachine in self.stateMachines:
        #         self.stateMachines[stateMachine]['starts'].append((match[0]))



    def print_extracted_info(self):
        for sm, info in self.stateMachines.items():
            print(f"State Machine: {sm}")
            print("  States:")
            for state in info['states']:
                print(f"    {state}")
            print("  Transitions:")
            for transition in info['transitions']:
                print(f"    {transition[0]} -> {transition[1]} on {transition[2]}")
            print("  Properties:")
            for prop in info['properties']:
                print(f"    {prop[0]} assigns {prop[1]} = {prop[2]}")
            print("  Connections:")
            for connection in info['connections']:
                print(f"    {connection[0]}::{connection[1]} -> {connection[2]}::{connection[3]}")
            print("  Initial States:")
            for initialState in info['initialStates']:
                print(f"    {initialState}")
            print("  Starts:")
            for start in info['starts']:
                print(f"    {start}")


    def getStates(self, machine=None):
        if machine:
            return self.stateMachines[machine]['states']
        # return a combined list of all states
        states = []
        for machine in self.stateMachines.values():
            states.extend(machine['states'])
        # filter out duplicates
        return list(set(states))
    
    def getTransitions(self, machine=None):
        if machine:
            return self.stateMachines[machine]['transitions']
        # return a combined list of all transitions
        transitions = []
        for machine in self.stateMachines.values():
            transitions.extend(machine['transitions'])
        # filter out duplicates
        return list(set(transitions))

    def getMachines(self):
        return self.stateMachines.keys() 
        
    def printExtractedInfo(self):
        for transition in self.transitions:
            print(f"Transition: {transition[0]} -> {transition[4]} on {transition[2]}::{transition[3]}")

        for prop in self.properties:
            print(f"Property: {prop[0]} assigns {prop[2]} = {prop[3]}")

        for connection in self.connections:
            print(f"Connection: {connection[0]}::{connection[2]} -> {connection[3]}::{connection[5]}")

        for state in self.states:
            print(f"State added: {state[1]} to {state[0]}")

        for initialState in self.initialStates:
            print(f"Initial state: {initialState[1]} for {initialState[0]}")

        for start in self.starts:
            print(f"State machine {start[0]} started")




if __name__ == "__main__":
    arg_parser = argparse.ArgumentParser(description="Parse a cpp file for Qt statemachines and generate a DOT file.")
    arg_parser.add_argument('--file', type=str, required=True, help='The cpp  file to parse for Qt state machine ')
    arg_parser.add_argument('--outputdir', type=str, required=False, help='Output directory, default is current dir')
    arg_parser.add_argument('--visualize', type=bool, required=False, default=False, help='Show the diagram in a window using Graphiz')
    
    args = arg_parser.parse_args()


    parser = QtStateMachineParser(args.file)
    parser.parse()

    
    filename =   os.path.basename(args.file)
    output_prefix = f"diagram_{filename}"
    visual = args.visualize
    if args.outputdir:
        if not os.path.exists(args.outputdir):
            os.makedirs(args.outputdir)
        output_prefix = os.path.join(args.outputdir, output_prefix)
        
    for machine in parser.getMachines():
        
        diagram = Diagram()
        states= parser.getStates(machine)
        diagram.addStates(states)
        transitions = parser.getTransitions(machine)
        diagram.addTransitions(transitions)
        diagram.toDot(f"{output_prefix}_{machine}.dot", verbose = True, visualize = visual)
