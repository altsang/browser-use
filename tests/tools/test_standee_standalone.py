#!/usr/bin/env python3
"""
Standalone testing script for the Standee Detection Tool.

This script provides comprehensive testing of the standee detection tool
independently of the browser-use agent system. It tests all major functionality
including model loading, image processing, detection logic, and MCP integration.

Usage:
    python tests/tools/test_standee_standalone.py
    
Requirements:
    - YOLOv8 model file at expected location
    - Test images in tests/tools/test_images/
    - ultralytics, opencv-python, numpy packages
"""

import os
import sys
import time
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    from browser_use.tools.standee_detection import StandeeDetectionTool
    from browser_use.tools.registry import ToolRegistry
except ImportError as e:
    print(f"Error importing browser-use tools: {e}")
    print("Make sure you're running from the project root and dependencies are installed")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StandeeDetectionTester:
    """Comprehensive tester for the standee detection tool."""
    
    def __init__(self):
        """Initialize the tester."""
        self.tool = None
        self.test_results = {
            'model_loading': False,
            'image_processing_bytes': False,
            'image_processing_url': False,
            'mcp_integration': False,
            'error_handling': False,
            'performance': {}
        }
        self.test_image_dir = Path(__file__).parent / "test_images"
        self.model_path = project_root / "models" / "yolov8" / "runs" / "standee_detection_train" / "weights" / "best.pt"
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are available."""
        logger.info("Checking prerequisites...")
        
        # Check model file
        if not self.model_path.exists():
            logger.error(f"YOLOv8 model not found at: {self.model_path}")
            return False
        logger.info(f"✓ Found YOLOv8 model at: {self.model_path}")
        
        # Check test images
        if not self.test_image_dir.exists():
            logger.error(f"Test image directory not found at: {self.test_image_dir}")
            return False
        
        test_images = list(self.test_image_dir.glob("*.png"))
        if not test_images:
            logger.error(f"No test images found in: {self.test_image_dir}")
            return False
        logger.info(f"✓ Found {len(test_images)} test images")
        
        # Check dependencies
        try:
            import ultralytics
            import cv2
            import numpy as np
            logger.info("✓ All required packages available")
        except ImportError as e:
            logger.error(f"Missing required package: {e}")
            return False
            
        return True
    
    def test_model_loading(self) -> bool:
        """Test model loading and initialization."""
        logger.info("\n" + "="*60)
        logger.info("TESTING MODEL LOADING AND INITIALIZATION")
        logger.info("="*60)
        
        try:
            # Test initialization with explicit model path
            logger.info("Testing tool initialization with explicit model path...")
            self.tool = StandeeDetectionTool(model_path=str(self.model_path))
            logger.info("✓ Tool initialized successfully")
            
            # Test model loading
            logger.info("Testing model loading...")
            start_time = time.time()
            model = self.tool.load_model()
            load_time = time.time() - start_time
            
            if model is None:
                logger.error("✗ Model loading failed")
                return False
                
            logger.info(f"✓ Model loaded successfully in {load_time:.2f} seconds")
            self.test_results['performance']['model_load_time'] = load_time
            
            # Test model properties
            logger.info("Testing model properties...")
            logger.info(f"  Model path: {self.tool.model_path}")
            logger.info(f"  Confidence threshold: {self.tool.confidence_threshold}")
            logger.info(f"  Model type: {type(model)}")
            
            self.test_results['model_loading'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Model loading test failed: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def test_image_processing_bytes(self) -> bool:
        """Test image processing from bytes."""
        logger.info("\n" + "="*60)
        logger.info("TESTING IMAGE PROCESSING FROM BYTES")
        logger.info("="*60)
        
        if not self.tool:
            logger.error("Tool not initialized")
            return False
            
        try:
            test_images = list(self.test_image_dir.glob("*.png"))
            if not test_images:
                logger.error("No test images available")
                return False
            
            for test_image in test_images:
                logger.info(f"\nTesting with image: {test_image.name}")
                
                # Read image bytes
                with open(test_image, "rb") as f:
                    image_bytes = f.read()
                
                # Test detection
                start_time = time.time()
                result = self.tool.detect_from_bytes(image_bytes)
                detection_time = time.time() - start_time
                
                # Log results
                logger.info(f"  Detection time: {detection_time:.2f} seconds")
                logger.info(f"  Success: {result.get('success', False)}")
                
                if result.get('success'):
                    detections = result.get('detections', [])
                    logger.info(f"  Detections found: {len(detections)}")
                    
                    for i, detection in enumerate(detections):
                        logger.info(f"    Detection {i+1}:")
                        logger.info(f"      Confidence: {detection.get('confidence', 0):.3f}")
                        logger.info(f"      Bbox: {detection.get('bbox', [])}")
                        logger.info(f"      Dimensions: {detection.get('width', 0):.1f} x {detection.get('height', 0):.1f}")
                        logger.info(f"      Aspect ratio: {detection.get('aspect_ratio', 0):.2f}")
                else:
                    logger.warning(f"  Error: {result.get('error', 'Unknown error')}")
                
                self.test_results['performance'][f'{test_image.name}_detection_time'] = detection_time
            
            self.test_results['image_processing_bytes'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Image processing (bytes) test failed: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def test_image_processing_url(self) -> bool:
        """Test image processing from URL."""
        logger.info("\n" + "="*60)
        logger.info("TESTING IMAGE PROCESSING FROM URL")
        logger.info("="*60)
        
        if not self.tool:
            logger.error("Tool not initialized")
            return False
            
        try:
            # Test with a sample URL (this is a public test image)
            test_url = "https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/assets/bus.jpg"
            
            logger.info(f"Testing with URL: {test_url}")
            
            start_time = time.time()
            result = self.tool.detect_from_url(test_url)
            detection_time = time.time() - start_time
            
            logger.info(f"  Detection time: {detection_time:.2f} seconds")
            logger.info(f"  Success: {result.get('success', False)}")
            
            if result.get('success'):
                detections = result.get('detections', [])
                logger.info(f"  Detections found: {len(detections)}")
            else:
                logger.warning(f"  Error: {result.get('error', 'Unknown error')}")
            
            self.test_results['performance']['url_detection_time'] = detection_time
            self.test_results['image_processing_url'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Image processing (URL) test failed: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def test_mcp_integration(self) -> bool:
        """Test MCP protocol compliance and metadata."""
        logger.info("\n" + "="*60)
        logger.info("TESTING MCP PROTOCOL INTEGRATION")
        logger.info("="*60)
        
        if not self.tool:
            logger.error("Tool not initialized")
            return False
            
        try:
            # Test metadata
            logger.info("Testing tool metadata...")
            metadata = self.tool.metadata
            
            required_fields = ['name', 'description', 'parameters', 'returns', 'version']
            for field in required_fields:
                if field not in metadata:
                    logger.error(f"  ✗ Missing required metadata field: {field}")
                    return False
                logger.info(f"  ✓ {field}: {type(metadata[field])}")
            
            # Test capabilities
            logger.info("\nTesting capabilities...")
            base_context = {}
            base_capabilities = self.tool.get_capabilities(base_context)
            logger.info(f"  Base capabilities: {base_capabilities}")
            
            gallery_context = {"in_photo_gallery": True}
            gallery_capabilities = self.tool.get_capabilities(gallery_context)
            logger.info(f"  Gallery capabilities: {gallery_capabilities}")
            
            restaurant_context = {"in_restaurant_page": True}
            restaurant_capabilities = self.tool.get_capabilities(restaurant_context)
            logger.info(f"  Restaurant capabilities: {restaurant_capabilities}")
            
            # Test examples
            logger.info("\nTesting examples...")
            examples = self.tool.get_examples()
            logger.info(f"  Number of examples: {len(examples)}")
            
            for i, example in enumerate(examples):
                required_example_fields = ['description', 'params', 'context', 'expected_result']
                for field in required_example_fields:
                    if field not in example:
                        logger.error(f"  ✗ Example {i+1} missing field: {field}")
                        return False
                logger.info(f"  ✓ Example {i+1}: {example['description']}")
            
            # Test execute method
            logger.info("\nTesting execute method...")
            test_params = {
                "image_url": "https://raw.githubusercontent.com/ultralytics/ultralytics/main/ultralytics/assets/bus.jpg"
            }
            test_context = {"in_restaurant_page": True}
            
            execute_result = self.tool.execute(test_params, test_context)
            logger.info(f"  Execute result success: {execute_result.get('success', False)}")
            
            self.test_results['mcp_integration'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ MCP integration test failed: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def test_error_handling(self) -> bool:
        """Test error handling scenarios."""
        logger.info("\n" + "="*60)
        logger.info("TESTING ERROR HANDLING")
        logger.info("="*60)
        
        if not self.tool:
            logger.error("Tool not initialized")
            return False
            
        try:
            # Test with invalid URL
            logger.info("Testing with invalid URL...")
            invalid_url_result = self.tool.detect_from_url("https://invalid-url-that-does-not-exist.com/image.jpg")
            if invalid_url_result.get('success'):
                logger.error("  ✗ Should have failed with invalid URL")
                return False
            logger.info(f"  ✓ Correctly failed: {invalid_url_result.get('error', '')}")
            
            # Test with invalid bytes
            logger.info("Testing with invalid image bytes...")
            invalid_bytes_result = self.tool.detect_from_bytes(b"not an image")
            if invalid_bytes_result.get('success'):
                logger.error("  ✗ Should have failed with invalid bytes")
                return False
            logger.info(f"  ✓ Correctly failed: {invalid_bytes_result.get('error', '')}")
            
            # Test execute with missing parameters
            logger.info("Testing execute with missing parameters...")
            missing_params_result = self.tool.execute({}, {})
            if missing_params_result.get('success'):
                logger.error("  ✗ Should have failed with missing parameters")
                return False
            logger.info(f"  ✓ Correctly failed: {missing_params_result.get('error', '')}")
            
            self.test_results['error_handling'] = True
            return True
            
        except Exception as e:
            logger.error(f"✗ Error handling test failed: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def test_performance_benchmarks(self) -> bool:
        """Run performance benchmarks."""
        logger.info("\n" + "="*60)
        logger.info("RUNNING PERFORMANCE BENCHMARKS")
        logger.info("="*60)
        
        if not self.tool:
            logger.error("Tool not initialized")
            return False
            
        try:
            test_images = list(self.test_image_dir.glob("*.png"))
            if not test_images:
                logger.warning("No test images available for benchmarking")
                return True
            
            # Run multiple iterations for more accurate timing
            iterations = 3
            times = []
            
            for iteration in range(iterations):
                logger.info(f"\nBenchmark iteration {iteration + 1}/{iterations}")
                iteration_times = []
                
                for test_image in test_images:
                    with open(test_image, "rb") as f:
                        image_bytes = f.read()
                    
                    start_time = time.time()
                    result = self.tool.detect_from_bytes(image_bytes)
                    detection_time = time.time() - start_time
                    
                    iteration_times.append(detection_time)
                    logger.info(f"  {test_image.name}: {detection_time:.3f}s")
                
                avg_time = sum(iteration_times) / len(iteration_times)
                times.append(avg_time)
                logger.info(f"  Average: {avg_time:.3f}s")
            
            overall_avg = sum(times) / len(times)
            logger.info(f"\nOverall average detection time: {overall_avg:.3f}s")
            
            self.test_results['performance']['benchmark_avg_time'] = overall_avg
            self.test_results['performance']['benchmark_iterations'] = iterations
            
            return True
            
        except Exception as e:
            logger.error(f"✗ Performance benchmark failed: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    def run_all_tests(self) -> bool:
        """Run all tests and return overall success."""
        logger.info("STARTING COMPREHENSIVE STANDEE DETECTION TOOL TESTING")
        logger.info("=" * 80)
        
        # Check prerequisites
        if not self.check_prerequisites():
            logger.error("Prerequisites check failed - cannot continue")
            return False
        
        # Run all tests
        tests = [
            ("Model Loading", self.test_model_loading),
            ("Image Processing (Bytes)", self.test_image_processing_bytes),
            ("Image Processing (URL)", self.test_image_processing_url),
            ("MCP Integration", self.test_mcp_integration),
            ("Error Handling", self.test_error_handling),
            ("Performance Benchmarks", self.test_performance_benchmarks)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            logger.info(f"\nRunning test: {test_name}")
            try:
                if test_func():
                    logger.info(f"✓ {test_name} PASSED")
                    passed_tests += 1
                else:
                    logger.error(f"✗ {test_name} FAILED")
            except Exception as e:
                logger.error(f"✗ {test_name} FAILED with exception: {str(e)}")
        
        # Print final summary
        self.print_summary(passed_tests, total_tests)
        
        return passed_tests == total_tests
    
    def print_summary(self, passed_tests: int, total_tests: int):
        """Print test summary."""
        logger.info("\n" + "="*80)
        logger.info("TEST SUMMARY")
        logger.info("="*80)
        
        logger.info(f"Tests passed: {passed_tests}/{total_tests}")
        logger.info(f"Success rate: {(passed_tests/total_tests)*100:.1f}%")
        
        logger.info("\nTest Results:")
        for test_name, result in self.test_results.items():
            if test_name == 'performance':
                continue
            status = "✓ PASS" if result else "✗ FAIL"
            logger.info(f"  {test_name}: {status}")
        
        logger.info("\nPerformance Metrics:")
        for metric, value in self.test_results['performance'].items():
            if isinstance(value, float):
                logger.info(f"  {metric}: {value:.3f}s")
            else:
                logger.info(f"  {metric}: {value}")
        
        if passed_tests == total_tests:
            logger.info("\n🎉 ALL TESTS PASSED! The standee detection tool is working correctly.")
        else:
            logger.warning(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Check the logs above for details.")


def main():
    """Main entry point."""
    tester = StandeeDetectionTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()