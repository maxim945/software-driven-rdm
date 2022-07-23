import jinja2
import json
import os

from enum import Enum
from importlib import resources as pkg_resources

from sdRDM.generator import templates as jinja_templates
from sdRDM.generator.abstractparser import SchemaParser
from sdRDM.generator.markdownparser import MarkdownParser


class Format(Enum):

    MARKDOWN = "md"


PARSER_MAPPING = {Format.MARKDOWN: MarkdownParser}


def generate_schema(handle, out: str, format: Format):
    """
    Converts a markdown specification file to a Mermaid Class Definition and metadata that
    in turn can be used to generate an API from.

    Args:
        path (str): Path to the Markdown file
        out (str): Destination of the resulting Mermaid and Metadata JSON file
    """

    # Set up and execute parser
    parser: SchemaParser = PARSER_MAPPING[format].parse(handle)

    template = jinja2.Template(
        pkg_resources.read_text(jinja_templates, "mermaid_class.jinja2")
    )
    mermaid_string = template.render(
        inherits=parser.inherits, compositions=parser.compositions, classes=parser.objs
    )

    # Create dirs if not already created
    os.makedirs(out, exist_ok=True)

    # Set paths for each file
    name = parser.module_name
    mermaid_path = os.path.join(out, f"{name}.md")
    metadata_path = os.path.join(out, f"{name}_metadata.json")

    with open(mermaid_path, "w") as file:
        file.write(mermaid_string)

    with open(metadata_path, "w") as file:
        file.write(write_metadata(parser.objs, parser.module_docstring))

    return mermaid_path, metadata_path


def write_metadata(definitions, module_doc) -> str:
    module_objs = {"docstring": module_doc}
    for obj in definitions:
        attr_meta = {}
        for attr in obj["attributes"]:

            # Build new dictionary w/o mermaid attrs
            attr_name = attr["name"]
            mermaid_keys = [
                "required",
                "type",
                "name",
            ]
            attr_meta[attr_name] = {
                key: item for key, item in attr.items() if key not in mermaid_keys
            }

        module_objs[obj.get("name")] = {
            "attributes": attr_meta,
            "docstring": obj.get("docstring"),
        }

    return json.dumps(module_objs, indent=2)


if __name__ == "__main__":
    print(os.getcwd())
    generate_schema("specifications/biocatalyst.md", ".", Format.MARKDOWN)
