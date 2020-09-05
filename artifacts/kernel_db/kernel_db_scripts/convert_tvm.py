# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

"""
This script helps you to insert specific kernels (specs in json files) into our kernel_db
Some more explains to customize it for your needs
    parameters : specify the parameters and their data types for a certain type of kernel
    gen_key    : generate identifier of kernel specification, including I/O shapes, types and more
    gen_config : convert kernel specification to the db format 
    insert_db  : insert the parsed kernel into kernel db
"""

import json
import sys
import sqlite3
import os
import math

from cuparse import parse as code_parse
from profile import prepare_file, profile, prod

db_path = os.environ['HOME'] + "/.cache/nnfusion/"
db_name = "kernel_cache.db"


# Todo: re-org operator definition to oop and coordinate to NNFusion
parameters = {
    "Convolution": {
        'symbol': ['input0', 'input1', 'output0'],
        'dtype': ['float*', 'float*', 'float*']
    },
    "MaxPool": {
        'symbol': ['input0', 'output0'],
        'dtype': ['float*', 'float*']
    },
    "Relu": {
        'symbol': ['input0', 'output0'],
        'dtype': ['float*', 'float*']
    },
    "Dot": {
        'symbol': ['input0', 'input1', 'output0'],
        'dtype': ['float*', 'float*', 'float*']
    },
    "Fused_Convolution_Relu": {
        'symbol': ['input0', 'input1', 'output0'],
        'dtype': ['float*', 'float*', 'float*']
    },
    "Fused_Convolution_Batchnorm_Relu": {
        'symbol': ['input0', 'input1', 'output0', 'input2'],
        'dtype': ['float*', 'float*', 'float*', 'float*']
    },
    "Fused_Convolution_Batchnorm": {
        'symbol': ['input0', 'input1', 'output0', 'input2'],
        'dtype': ['float*', 'float*', 'float*', 'float*']
    },
    "Fused_Convolution_Add_Relu": {
        'symbol': ['input0', 'input1', 'output0', 'input2'],
        'dtype': ['float*', 'float*', 'float*', 'float*']
    },
    "AvgPool": {
        'symbol': ['input0', 'output0'],
        'dtype': ['float*', 'float*']
    }
}


def gen_key(data, dtype="float"):
    op_type = data["op_type"]
    in_shape = data["in_shape"]
    out_shape = data["out_shape"]
    key = op_type
    key += "".join("".join(str(i) for i in shape) for shape in in_shape)
    if op_type != "Fused_Convolution_Add_Relu":
        key += "".join("".join(str(i) for i in shape) for shape in out_shape)
        key += "float" * (len(in_shape) + len(out_shape))
    else:
        key += "float" * len(in_shape)

    if op_type in [
            "Convolution", "Fused_Convolution_Relu", "Fused_Convolution_Batchnorm", "Fused_Convolution_Batchnorm_Relu",
            "Fused_Convolution_Add_Relu"
    ]:
        parameters = data["parameters"]
        key += "".join(["Strides{", ", ".join(str(i)
                                              for i in parameters["window_movement_strides"]), "}"])
        key += "".join(["Strides{", ", ".join(str(i)
                                              for i in parameters["window_dilation_strides"]), "}"])
        key += "".join(["CoordinateDiff{", ", ".join(str(i)
                                                     for i in parameters["padding_below_diff"]), "}"])
        if op_type != "Convolution":
            key = key.replace(op_type, "Convolution")
            for op in op_type.split("_"):
                if op == "Batchnorm":
                    raise ("to be specified")
                elif op == "Add":
                    key += "Add" + "".join("".join(str(i) for i in shape)
                                           for shape in out_shape) * 3 + "float" * 3 * len(out_shape)
                elif op == "Relu":
                    key += "Relu" + "".join("".join(str(i) for i in shape)
                                            for shape in out_shape) * 2 + "float" * 2 * len(out_shape)
                elif op not in ["Fused", "Convolution"]:
                    raise ("not implemented")
    elif op_type == "AvgPool" or op_type == "MaxPool":
        parameters = data["parameters"]
        key += "Shape{" + ", ".join(str(i)
                                    for i in parameters["window_shape"]) + "}"
        key += "Strides{" + ", ".join(str(i)
                                      for i in parameters["window_stride"]) + "}"
        key += "Shape{" + ", ".join(str(i)
                                    for i in parameters["padding_below"]) + "}"

    return key


def gen_config(op_type, kernel, shared_memory, num_sync):
    # the entries to retrive parameters depend on spec of json files
    config = {
        "op_type": op_type,
        "function_body": "",
        "shared_memory": shared_memory,
        "num_sync": num_sync,
        "blockDim": kernel["blockDim"],
        "gridDim": kernel["gridDim"],
    }
    if op_type in [
            "Convolution", "Fused_Convolution_Relu", "Fused_Convolution_Batchnorm", "Fused_Convolution_Batchnorm_Relu",
            "Fused_Convolution_Add_Relu"
    ]:
        config["function_sig"] = "extern \"C\" __global__  void (float* input0, float* input1, float* output0)"
        config["in_shape"] = [kernel["parameters"]
                              ["input_shape"], kernel["parameters"]["filter_shape"]]
        config["out_shape"] = [kernel["parameters"]["output_shape"]]
        config["parameters"] = {
            "window_movement_strides": kernel["parameters"]["window_movement_strides"],
            "window_dilation_strides": kernel["parameters"]["window_dilation_strides"],
            "padding_below_diff": kernel["parameters"]["padding_below_diff"]
        }
        if "Batchnorm" in op_type or "Add" in op_type:
            if "Batchnorm" in op_type and "Add" in op_type:
                config[
                    "function_sig"] = "extern \"C\" __global__  void (float* input0, float* input1, float* input2, float* input3, float* output0)"
            else:
                config["in_shape"].append(config["out_shape"][0])
                config[
                    "function_sig"] = "extern \"C\" __global__  void (float* input0, float* input1, float* input2, float* output0)"
    elif (op_type == "Dot"):
        config["in_shape"] = [kernel["parameters"]
                              ["arg0_shape"], kernel["parameters"]["arg1_shape"]]
        config["out_shape"] = [kernel["parameters"]["out_shape"]]
        config[
            "function_sig"] = "extern \"C\" __global__  void (float* __restrict__ input0,  float* __restrict__ input1,  float* __restrict__ output0)"
    elif (op_type == "Relu"):
        config["in_shape"] = [kernel["parameters"]["input_shape"]]
        config["out_shape"] = [kernel["parameters"]["output_shape"]]
        config["function_sig"] = "extern \"C\" __global__  void (float* input0, float* output0)"
    elif (op_type == "AvgPool" or op_type == "MaxPool"):
        config["in_shape"] = [kernel["parameters"]["input_shape"]]
        config["out_shape"] = [kernel["parameters"]["output_shape"]]
        config["function_sig"] = "extern \"C\" __global__  void (float* input0, float* output0)"
        config["parameters"] = {
            "window_shape": kernel["parameters"]["window_shape"],
            "window_stride": kernel["parameters"]["window_stride"],
            "padding_below": kernel["parameters"]["padding_below"]
        }
    else:
        raise ("not implemented")

    return config


def insert_db(name, platform="CUDA", tags="fast", profile="Tesla V100-PCIE-16GB:1", resource=0):
    # Todo: More tags could be used to store multiple implementations with the same kernel specs
    in_file = open(name + ".cu")
    json_file = open(name + ".json")

    data = json.load(json_file)
    function_body = in_file.read()
    data["function_body"] = function_body

    function = json.dumps(data)
    conn = sqlite3.connect(db_path + db_name)
    c = conn.cursor()

    create_sql = "create table if not exists KernelCache (\
            identifier TEXT NOT NULL,\
            platform   TEXT NOT NULL,\
            function   TEXT NOT NULL,\
            tags       TEXT DEFAULT '',\
            profile    TEXT DEFAULT '',\
            resource   INTEGER NOT NULL\
            )"

    c.execute(create_sql)

    identifier = gen_key(data)
    print(identifier)
    # overwrite the same implementation
    c.execute("DELETE FROM KernelCache WHERE identifier = ? AND platform = ? AND function = ?",
              (identifier, platform, function))
    c.execute("INSERT INTO KernelCache (identifier,platform,function,tags,profile,resource) VALUES (?, ?, ?, ?, ?, ?)",
              (identifier, platform, function, tags, profile, resource))
    conn.commit()
    conn.close()


if __name__ == '__main__':
    if not os.path.isdir(db_path):
        os.mkdir(db_path)
    json_file = open(sys.argv[1])
    kernels = json.load(json_file)
    # input json file could contain one or more kernels
    if "op_type" in kernels:
        kernels = [kernels]
    for kernel in kernels:
        op_type = kernel["op_type"]

        # parse and clean up the cuda code to get some specific information
        shared_memory, num_sync, new_code, signature = code_parse(
            kernel["code"], parameters[op_type])

        config = gen_config(op_type, kernel, shared_memory, num_sync)

        # feel free to customize the repo name you want
        name = kernel["tvm_func_name"].replace("_kernel0", "")
        operator_path = db_path + op_type + "_db/"
        if not os.path.isdir(operator_path):
            os.mkdir(operator_path)
        with open(operator_path + name + ".json", "w+") as f:
            json.dump(config, f)
        with open(operator_path + name + ".cu", "w+") as f:
            f.write(new_code)

        default_tags = "fast"
        if (op_type == "Dot"):
            default_tags += kernel["parameters"]["transpose_A"] * \
                ",transA" + kernel["parameters"]["transpose_B"]*",transB"

        # apply rules that every 32 threads will be formed as a warp
        resource = math.ceil(
            prod(config["blockDim"])/32)*32 * prod(config["gridDim"])
        prepare_file(signature, kernel["code"], config, db_path + "profile/")
        profile_info = profile(signature, db_path + "profile/")
        print(profile_info, resource)
        insert_db(operator_path + name,
                  tags=default_tags, profile=profile_info, resource=resource)
