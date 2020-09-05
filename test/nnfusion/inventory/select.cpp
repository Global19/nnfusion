// Copyright (c) Microsoft Corporation.
// Licensed under the MIT License.

/**
 * \brief Unit tests for ir::Select
 * \author generated by script
 */

#include "../test_util/common.hpp"

namespace nnfusion
{
    namespace test
    {
        template <typename T, size_t N>
        using NDArray = nnfusion::test::NDArray<T, N>;
    }

    namespace inventory
    {
        template <>
        shared_ptr<graph::GNode> create_object<op::Select, float>(int option)
        {
            switch (option)
            {
            case 0:
            {
                auto graph = std::make_shared<graph::Graph>();
                Shape shape{2, 2, 2};
                auto A = make_shared<op::Parameter>(element::boolean, shape);
                auto A_gnode = graph->add_node_and_edge(A, GNodeVector({}));
                auto B = make_shared<op::Parameter>(element::f32, shape);
                auto B_gnode = graph->add_node_and_edge(B, GNodeVector({}));
                auto C = make_shared<op::Parameter>(element::f32, shape);
                auto C_gnode = graph->add_node_and_edge(C, GNodeVector({}));
                auto r = make_shared<op::Select>();
                auto r_gnode = graph->add_node_and_edge(r, {A_gnode, B_gnode, C_gnode});
                return r_gnode;
            }
            default: return nullptr;
            }
        }

        template <>
        vector<float> generate_input<op::Select, float>(int option)
        {
            switch (option)
            {
            case 0:
            {
                vector<float> a = vector<float>{0, 1, 1, 0, 0, 1, 0, 1};
                vector<float> b = vector<float>{1, 2, 3, 4, 5, 6, 7, 8};
                vector<float> c = vector<float>{11, 12, 13, 14, 15, 16, 17, 18};
                auto return_vector = vector<float>();
                return_vector.insert(return_vector.end(), a.begin(), a.end());
                return_vector.insert(return_vector.end(), b.begin(), b.end());
                return_vector.insert(return_vector.end(), c.begin(), c.end());
                return return_vector;
            }
            default: return vector<float>();
            }
        }

        template <>
        vector<float> generate_output<op::Select, float>(int option)
        {
            switch (option)
            {
            case 0:
            {
                vector<float> result = vector<float>{11, 2, 3, 14, 15, 6, 17, 8};
                auto return_vector = vector<float>();
                return_vector.insert(return_vector.end(), result.begin(), result.end());
                return return_vector;
            }
            default: return vector<float>();
            }
        }
    }
}