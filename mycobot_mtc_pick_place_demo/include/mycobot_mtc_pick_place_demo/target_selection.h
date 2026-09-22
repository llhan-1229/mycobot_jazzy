#ifndef TARGET_SELECTION_H
#define TARGET_SELECTION_H

#include <string>
#include <vector>

#include "mycobot_mtc_pick_place_demo/object_segmentation.h"

struct TargetSelection {
  std::string object_id;
  double similarity{ 0.0 };
};

TargetSelection selectTargetObject(
    const std::vector<SegmentedObject>& objects,
    const std::string& target_shape,
    const std::vector<double>& target_dimensions,
    const std::string& target_color,
    double minimum_similarity,
    double minimum_color_confidence);

#endif  // TARGET_SELECTION_H
