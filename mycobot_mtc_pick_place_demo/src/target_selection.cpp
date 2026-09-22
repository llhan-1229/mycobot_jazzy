#include "mycobot_mtc_pick_place_demo/target_selection.h"

#include <algorithm>
#include <cmath>

#include <shape_msgs/msg/solid_primitive.hpp>

TargetSelection selectTargetObject(
    const std::vector<SegmentedObject>& objects,
    const std::string& target_shape,
    const std::vector<double>& target_dimensions,
    const std::string& target_color,
    double minimum_similarity,
    double minimum_color_confidence)
{
  TargetSelection selection;

  for (const auto& detected : objects) {
    if (detected.color != target_color ||
        detected.color_confidence < minimum_color_confidence ||
        detected.collision_object.primitives.empty()) {
      continue;
    }

    const auto& primitive = detected.collision_object.primitives.front();
    std::vector<double> dimensions;
    if (target_shape == "cylinder" &&
        primitive.type == shape_msgs::msg::SolidPrimitive::CYLINDER) {
      if (primitive.dimensions.size() <= shape_msgs::msg::SolidPrimitive::CYLINDER_RADIUS) {
        continue;
      }
      dimensions = {
        primitive.dimensions[shape_msgs::msg::SolidPrimitive::CYLINDER_HEIGHT],
        primitive.dimensions[shape_msgs::msg::SolidPrimitive::CYLINDER_RADIUS]
      };
    } else if (target_shape == "box" &&
               primitive.type == shape_msgs::msg::SolidPrimitive::BOX) {
      if (primitive.dimensions.size() <= shape_msgs::msg::SolidPrimitive::BOX_Z) {
        continue;
      }
      dimensions = {
        primitive.dimensions[shape_msgs::msg::SolidPrimitive::BOX_X],
        primitive.dimensions[shape_msgs::msg::SolidPrimitive::BOX_Y],
        primitive.dimensions[shape_msgs::msg::SolidPrimitive::BOX_Z]
      };
    } else {
      continue;
    }

    if (dimensions.size() != target_dimensions.size() ||
        std::any_of(target_dimensions.begin(), target_dimensions.end(),
                    [](double value) { return value <= 0.0; })) {
      continue;
    }

    double normalized_difference = 0.0;
    for (std::size_t i = 0; i < dimensions.size(); ++i) {
      normalized_difference += std::abs(dimensions[i] - target_dimensions[i]) /
                               target_dimensions[i];
    }
    const double dimension_score = std::max(
      0.0, 1.0 - normalized_difference / dimensions.size());
    const double similarity = 0.7 + 0.3 * dimension_score;

    if (similarity > selection.similarity) {
      selection.object_id = detected.collision_object.id;
      selection.similarity = similarity;
    }
  }

  if (selection.similarity < minimum_similarity) {
    return {};
  }
  return selection;
}
