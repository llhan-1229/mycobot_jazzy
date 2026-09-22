#include <gtest/gtest.h>

#include <cstdint>
#include <string>
#include <vector>

#include "mycobot_mtc_pick_place_demo/object_segmentation.h"
#include "mycobot_mtc_pick_place_demo/target_selection.h"

namespace {

pcl::PointCloud<PointXYZRGBNormalRSD>::Ptr makeCluster(
    const std::vector<std::tuple<std::uint8_t, std::uint8_t, std::uint8_t>>& colors)
{
  auto cluster = std::make_shared<pcl::PointCloud<PointXYZRGBNormalRSD>>();
  for (const auto& [red, green, blue] : colors) {
    PointXYZRGBNormalRSD point{};
    point.r = red;
    point.g = green;
    point.b = blue;
    cluster->push_back(point);
  }
  return cluster;
}

SegmentedObject makeCylinder(
    const std::string& id, const std::string& color, double height, double radius)
{
  SegmentedObject object;
  object.collision_object.id = id;
  object.color = color;
  object.color_confidence = 1.0;
  shape_msgs::msg::SolidPrimitive primitive;
  primitive.type = shape_msgs::msg::SolidPrimitive::CYLINDER;
  primitive.dimensions = { height, radius };
  object.collision_object.primitives.push_back(primitive);
  return object;
}

TEST(ColorClassification, RecognizesRedAndBlue)
{
  const auto red = classifyClusterColor(makeCluster({ {255, 0, 0}, {220, 5, 5} }), 0.4, 0.1, 0.6);
  const auto blue = classifyClusterColor(makeCluster({ {0, 0, 255}, {5, 5, 220} }), 0.4, 0.1, 0.6);
  EXPECT_EQ(red.color, "red");
  EXPECT_DOUBLE_EQ(red.confidence, 1.0);
  EXPECT_EQ(blue.color, "blue");
  EXPECT_DOUBLE_EQ(blue.confidence, 1.0);
}

TEST(ColorClassification, HandlesDarkColorAndAchromaticNoise)
{
  const auto result = classifyClusterColor(
    makeCluster({ {0, 0, 70}, {0, 0, 90}, {100, 100, 100}, {240, 240, 240} }),
    0.4, 0.1, 0.6);
  EXPECT_EQ(result.color, "blue");
  EXPECT_EQ(result.chromatic_points, 2u);
  EXPECT_DOUBLE_EQ(result.confidence, 1.0);
}

TEST(ColorClassification, RejectsLowConfidenceAndUnsupportedColor)
{
  const auto low_confidence = classifyClusterColor(
    makeCluster({ {255, 0, 0}, {255, 0, 0}, {0, 0, 255}, {0, 255, 0} }),
    0.4, 0.1, 0.6);
  const auto green = classifyClusterColor(makeCluster({ {0, 255, 0} }), 0.4, 0.1, 0.6);
  EXPECT_EQ(low_confidence.color, "unknown");
  EXPECT_DOUBLE_EQ(low_confidence.confidence, 0.5);
  EXPECT_EQ(green.color, "unknown");
}

TEST(TargetSelection, SelectsRequestedColorFromSameSizedCylinders)
{
  const std::vector<SegmentedObject> objects = {
    makeCylinder("cylinder_0", "red", 0.35, 0.0125),
    makeCylinder("cylinder_1", "blue", 0.35, 0.0125),
  };
  EXPECT_EQ(selectTargetObject(objects, "cylinder", {0.35, 0.0125}, "red", 0.8, 0.6).object_id,
            "cylinder_0");
  EXPECT_EQ(selectTargetObject(objects, "cylinder", {0.35, 0.0125}, "blue", 0.8, 0.6).object_id,
            "cylinder_1");
}

TEST(TargetSelection, RejectsMissingColorAndBadDimensions)
{
  const std::vector<SegmentedObject> objects = {
    makeCylinder("cylinder_0", "red", 0.35, 0.0125),
    makeCylinder("cylinder_1", "blue", 2.0, 0.5),
  };
  EXPECT_TRUE(selectTargetObject(
    objects, "cylinder", {0.35, 0.0125}, "blue", 0.8, 0.6).object_id.empty());
  EXPECT_TRUE(selectTargetObject(
    objects, "cylinder", {0.35, 0.0125}, "green", 0.8, 0.6).object_id.empty());
}

TEST(TargetSelection, RejectsLowColorConfidence)
{
  auto object = makeCylinder("cylinder_0", "red", 0.35, 0.0125);
  object.color_confidence = 0.59;
  EXPECT_TRUE(selectTargetObject(
    { object }, "cylinder", {0.35, 0.0125}, "red", 0.8, 0.6).object_id.empty());
}

TEST(TargetSelection, RejectsIncompletePrimitiveDimensions)
{
  auto object = makeCylinder("cylinder_0", "red", 0.35, 0.0125);
  object.collision_object.primitives.front().dimensions.pop_back();
  EXPECT_TRUE(selectTargetObject(
    { object }, "cylinder", {0.35, 0.0125}, "red", 0.8, 0.6).object_id.empty());
}

}  // namespace
