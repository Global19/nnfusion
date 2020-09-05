//*****************************************************************************
// Copyright 2017-2020 Intel Corporation
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//*****************************************************************************


// Microsoft (c) 2019, NNFusion Team

#pragma once

#include <memory>

#include "nnfusion/core/operators/op.hpp"

namespace nnfusion
{
    namespace op
    {
        class ReverseSequence : public Op
        {
        public:
            /// \brief Constructs an arcsin operation.
            ///
            ReverseSequence(size_t batch_axis, size_t seq_axis);

            void validate_and_infer_types(std::shared_ptr<graph::GNode> gnode) override;

            size_t get_batch_axis() const { return m_batch_axis; }
            size_t get_sequence_axis() const { return m_seq_axis; }
        private:
            size_t m_batch_axis{0};
            size_t m_seq_axis{0};
        };
    }
}
