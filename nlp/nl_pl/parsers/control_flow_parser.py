from dataclasses import dataclass, field
from typing import List, Optional, Any, Dict
from enum import Enum
from .syntactic_parser import SyntacticParse
from .semantic_analyzer import SemanticAnalysis

class ControlFlowType(Enum):
    COMPOUND = "compound"
    CONDITIONAL = "conditional"
    LOOP = "loop"
    SEQUENCE = "sequence"
    SINGLE = "single"

@dataclass
class Command:
    action: str
    params: Dict[str, Any]
    raw_text: str

@dataclass
class ControlFlowNode:
    flow_type: ControlFlowType
    condition: Optional[str] = None
    commands: List[Command] = field(default_factory=list)
    children: List['ControlFlowNode'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ControlFlowStructure:
    root: ControlFlowNode
    flow_graph: List[ControlFlowNode]
    raw_text: str

class ControlFlowParser:
    def __init__(self, known_actions=None):
        self.conjunctions = ["and", "then", ","]
        self.conditionals = ["if", "when", "whenever", "unless"]
        self.loops = ["while", "until", "for", "repeat"]
        self.known_actions = set(known_actions) if known_actions else set()

    def parse(self, text: str, syntactic_parse: SyntacticParse, semantic_analysis: SemanticAnalysis) -> ControlFlowStructure:
        text_lower = text.lower()

        if any(cond in text_lower for cond in self.conditionals):
            root = self._parse_conditional(text, syntactic_parse, semantic_analysis)
        elif any(loop in text_lower for loop in self.loops):
            root = self._parse_loop(text, syntactic_parse, semantic_analysis)
        elif any(conj in text_lower for conj in self.conjunctions):
            root = self._parse_compound(text, syntactic_parse, semantic_analysis)
        else:
            root = self._parse_single(text, semantic_analysis)

        flow_graph = self._flatten_graph(root)

        return ControlFlowStructure(
            root=root,
            flow_graph=flow_graph,
            raw_text=text
        )

    def _parse_compound(self, text: str, syntactic_parse: SyntacticParse, semantic_analysis: SemanticAnalysis) -> ControlFlowNode:
        node = ControlFlowNode(flow_type=ControlFlowType.COMPOUND)

        segments = self._split_by_conjunctions(text)

        for segment in segments:
            command = self._extract_command_from_segment(segment, semantic_analysis)
            if command:
                child_node = ControlFlowNode(
                    flow_type=ControlFlowType.SINGLE,
                    commands=[command]
                )
                node.children.append(child_node)

        return node

    def _parse_conditional(self, text: str, syntactic_parse: SyntacticParse, semantic_analysis: SemanticAnalysis) -> ControlFlowNode:
        node = ControlFlowNode(flow_type=ControlFlowType.CONDITIONAL)

        condition_keyword = None
        for keyword in self.conditionals:
            if keyword in text.lower():
                condition_keyword = keyword
                break

        if condition_keyword:
            parts = text.lower().split(condition_keyword, 1)
            if len(parts) == 2:
                condition_part = parts[1].strip()

                condition_end_markers = [" then ", ",", " and "]
                condition_text = condition_part
                action_text = ""

                for marker in condition_end_markers:
                    if marker in condition_part:
                        split_parts = condition_part.split(marker, 1)
                        condition_text = split_parts[0].strip()
                        action_text = split_parts[1].strip()
                        break

                node.condition = condition_text
                node.metadata["condition_keyword"] = condition_keyword

                if action_text:
                    command = self._extract_command_from_segment(action_text, semantic_analysis)
                    if command:
                        node.commands.append(command)

        return node

    def _parse_loop(self, text: str, syntactic_parse: SyntacticParse, semantic_analysis: SemanticAnalysis) -> ControlFlowNode:
        node = ControlFlowNode(flow_type=ControlFlowType.LOOP)

        loop_keyword = None
        for keyword in self.loops:
            if keyword in text.lower():
                loop_keyword = keyword
                break

        if loop_keyword:
            parts = text.lower().split(loop_keyword, 1)
            if len(parts) == 2:
                condition_and_action = parts[1].strip()

                condition_end_markers = [" do ", ",", " then "]
                condition_text = condition_and_action
                action_text = ""

                for marker in condition_end_markers:
                    if marker in condition_and_action:
                        split_parts = condition_and_action.split(marker, 1)
                        condition_text = split_parts[0].strip()
                        action_text = split_parts[1].strip()
                        break

                node.condition = condition_text
                node.metadata["loop_keyword"] = loop_keyword

                if action_text:
                    command = self._extract_command_from_segment(action_text, semantic_analysis)
                    if command:
                        node.commands.append(command)

        return node

    def _parse_single(self, text: str, semantic_analysis: SemanticAnalysis) -> ControlFlowNode:
        command = self._extract_command_from_segment(text, semantic_analysis)
        return ControlFlowNode(
            flow_type=ControlFlowType.SINGLE,
            commands=[command] if command else []
        )

    def _split_by_conjunctions(self, text: str) -> List[str]:
        segments = [text]

        for conj in self.conjunctions:
            new_segments = []
            for segment in segments:
                parts = segment.split(f" {conj} ")
                new_segments.extend([p.strip() for p in parts])
            segments = new_segments

        return [s for s in segments if s]

    def _extract_command_from_segment(self, segment: str, semantic_analysis: SemanticAnalysis) -> Optional[Command]:
        from .syntactic_parser import SyntacticParser
        from .semantic_analyzer import SemanticAnalyzer

        syntactic_parser = SyntacticParser()
        semantic_analyzer = SemanticAnalyzer(known_actions=self.known_actions)

        segment_syntax = syntactic_parser.parse(segment)
        segment_semantics = semantic_analyzer.analyze(segment_syntax)

        if not segment_semantics.frames:
            return Command(action="unknown", params={}, raw_text=segment)

        frame = segment_semantics.frames[0]

        params = {}
        for role, value in frame.roles.items():
            if role.value != "action":
                params[role.value] = value

        return Command(
            action=frame.action,
            params=params,
            raw_text=segment
        )

    def _flatten_graph(self, node: ControlFlowNode) -> List[ControlFlowNode]:
        result = [node]
        for child in node.children:
            result.extend(self._flatten_graph(child))
        return result

    def get_execution_order(self, structure: ControlFlowStructure) -> List[Command]:
        commands = []
        self._collect_commands_recursive(structure.root, commands)
        return commands

    def _collect_commands_recursive(self, node: ControlFlowNode, commands: List[Command]):
        commands.extend(node.commands)
        for child in node.children:
            self._collect_commands_recursive(child, commands)
