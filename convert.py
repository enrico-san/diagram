from unittest import loader
import xmlplain
import sys
import json
import yaml

lambda_template = {
    "Type": "Task",
    "Resource": "${TodoLambdaArn}",
    "Retry": [
        {
        "ErrorEquals": [
            "ValidatorException",
            "SchemaValidationError"
        ],
        "MaxAttempts": 0,
        "Comment": "Skip retry for specified exceptions"
        },
        {
        "ErrorEquals": [
            "PriceCalculatorError"
        ],
        "IntervalSeconds": 1000,
        "MaxAttempts": 20,
        "BackoffRate": 1.5,
        "Comment": "Approximately 1 month and 1 week"
        },

        {
        "ErrorEquals": [
            "States.ALL"
        ],
        "IntervalSeconds": 300,
        "MaxAttempts": 50,
        "BackoffRate": 1.25,
        "Comment": "Approximately 8 month"
        }
    ],
    "Catch": [
        {
        "ErrorEquals": [
            "ValidatorException",
            "SchemaValidationError",
            "PriceCalculatorError"
        ],
        "Next": "Execution Fail",
        "Comment": "Stop execution for specified exceptions"
        }
    ],
    "End": True
}

def converter(what, FROM, TO):
    if what == 'xml-yaml':
        with open(FROM) as inf:
            root = xmlplain.xml_to_obj(inf, strip_space=True, fold_dict=True)

        with open(TO, "w") as outf:
            xmlplain.obj_to_yaml(root, outf)

    elif what == 'json-yaml':
        with open(FROM) as inf:
            root = json.load(inf)

        with open(TO, "w") as outf:
            yaml.dump(root, outf, Dumper=yaml.Dumper)

    elif what == 'yaml-json':
        with open(FROM) as inf:
            root = yaml.load(inf, Loader=yaml.FullLoader)

        with open(TO, "w") as outf:
            json.dump(root, outf)

    elif what == 'xml-step':
        converter('xml-yaml', FROM, '_intermediate.yaml')

        with open('_intermediate.yaml') as inf:
            root = yaml.load(inf, Loader=yaml.FullLoader)

        step_function = {'States': [{'Execution Fail': {'Type': 'Fail'}}]}
        start = state = None
        for element in root['bpmn:definitions']['bpmn:process']:
            block = list(element.keys())[0]
            
            if block == 'bpmn:startEvent':
                start = element[block]['bpmn:outgoing']

            if block == 'bpmn:task':
                state = element[block]['@name']
                if element[block]['bpmn:incoming'] == start:
                    start = state
                    step_function['StartAt'] = start
                
                step_function[state] = lambda_template.copy()

        with open(TO, "w") as outf:
            json.dump(step_function, outf, indent=4)

if __name__ == '__main__':
    what = sys.argv[1]
    FROM = sys.argv[2]
    TO = sys.argv[3]

    converter(what, FROM, TO)
