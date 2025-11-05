import sys
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

from nl_pl.interface import NaturalLanguageInterface


def main(source_file=None, class_name=None, queries=None):
    if source_file is None:
        source_file = os.path.join(parent_dir, "source_kbs", "smarthome.py")
    if class_name is None:
        class_name = "SmartHome"
    if queries is None:
        queries = ["turn off the ac"]

    interface = NaturalLanguageInterface(
        python_file=source_file,
        class_name=class_name,
        output_dir=os.path.join(current_dir, "output")
    )

    interface.export_ast_analysis()
    
    object_name = interface.get_object_name_for_class(class_name)

    results = []
    for text in queries:
        method_name, params, result = interface.process(text, export_json=True)

        if method_name:
            if params:
                param_str = ", ".join([f"{k}={repr(v)}" for k, v in params.items()])
                results.append(f"{object_name}.{method_name}({param_str})")
            else:
                results.append(f"{object_name}.{method_name}()")

        elif result['method_resolution']['metadata'] and 'resolved_commands' in result['method_resolution']['metadata']:
            commands = []
            for cmd in result['method_resolution']['metadata']['resolved_commands']:
                if cmd['params']:
                    param_str = ", ".join([f"{k}={repr(v)}" for k, v in cmd['params'].items()])
                    commands.append(f"{object_name}.{cmd['method']}({param_str})")
                else:
                    commands.append(f"{object_name}.{cmd['method']}()")
            results.extend(commands)

        else:
            error = result['method_resolution']['metadata'].get('error')
            if error == "ambiguous":
                suggestions = result['method_resolution']['metadata'].get('suggestions', [])
                margin = result['method_resolution']['metadata'].get('margin', 0)
                confidence = result['method_resolution']['metadata'].get('confidence', 0)
                
                error_msg = f"Error: {error} (confidence: {confidence:.2f}, margin: {margin:.2f})"
                results.append(error_msg)
                results.append("Possible matches:")
                for suggestion in suggestions:
                    results.append(f"  - {suggestion['method']} (score: {suggestion['score']:.2f}) - '{suggestion['phrase']}'")
            else:
                results.append(f"Error: {error}")
    
    return results


if __name__ == "__main__":
    if len(sys.argv) >= 2:
        source_file = sys.argv[1]
        class_name = sys.argv[2] if len(sys.argv) >= 3 else None
        queries = [sys.argv[3]] if len(sys.argv) >= 4 else None
        output = main(source_file, class_name, queries)
    else:
        output = main()
    
    for result in output:
        print(result)
