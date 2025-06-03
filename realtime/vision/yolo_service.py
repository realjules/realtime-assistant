import logging
import json
import cv2
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
import base64
import io
from PIL import Image
from ultralytics import YOLO
import os

logger = logging.getLogger(__name__)

class YOLOService:
    def __init__(self, model_path: str = "yolov8n.pt"):
        """Initialize YOLO service with real YOLOv8 model"""
        self.model = None
        self.model_path = model_path
        self.output_dir = "yolo_outputs"
        
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Load model on initialization
        self.load_yolo_model()
    
    def load_yolo_model(self, model_path: Optional[str] = None):
        """Load YOLO model"""
        try:
            path = model_path or self.model_path
            logger.info(f"Loading YOLO model from {path}")
            self.model = YOLO(path)
            logger.info("YOLO model loaded successfully")
        except Exception as e:
            logger.error(f"Error loading YOLO model: {e}")
            raise
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process images with YOLO for product detection"""
        try:
            images = state.get("images", [])
            
            if not images or len(images) == 0:
                state["response"] = "No images provided for analysis."
                return state
            
            if not self.model:
                state["error"] = "YOLO model not loaded"
                state["response"] = "YOLO model is not available. Please check the setup."
                return state
            
            all_detections = []
            detection_metadata = {
                "timestamp": datetime.now().isoformat(),
                "image_count": len(images),
                "total_objects": 0,
                "processing_time": None
            }
            
            start_time = datetime.now()
            
            for i, image_data in enumerate(images):
                # Validate and preprocess image
                if not self._validate_image(image_data):
                    logger.warning(f"Invalid image format for image {i+1}")
                    continue
                
                # Convert bytes to image
                image = self._bytes_to_image(image_data)
                if image is None:
                    continue
                
                # Run YOLO detection
                detections = self._run_yolo_detection(image, image_index=i)
                all_detections.extend(detections)
            
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()
            detection_metadata["processing_time"] = f"{processing_time:.2f}s"
            detection_metadata["total_objects"] = len(all_detections)
            
            # Save results to JSON
            json_filename = self._save_detections_to_json(all_detections, detection_metadata)
            
            # Update state with detected products
            state["detected_products"] = all_detections
            
            if all_detections:
                # Format response for detected products
                response = self._format_detection_response(all_detections, detection_metadata, json_filename)
                state["response"] = response
                
                # Set flag to continue to customer agent for product matching
                context = state.get("conversation_context", {})
                context["has_detected_products"] = True
                context["json_output_file"] = json_filename
                context["detection_metadata"] = detection_metadata
                state["conversation_context"] = context
                
            else:
                state["response"] = self._format_no_detection_response()
            
        except Exception as e:
            logger.error(f"YOLO processing error: {e}")
            state["error"] = str(e)
            state["response"] = "Sorry, I had trouble analyzing your image. Please try again."
        
        return state
    
    def _bytes_to_image(self, image_data: bytes) -> Optional[np.ndarray]:
        """Convert bytes to OpenCV image"""
        try:
            # Convert bytes to PIL Image
            pil_image = Image.open(io.BytesIO(image_data))
            
            # Convert PIL to OpenCV format
            opencv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            return opencv_image
        except Exception as e:
            logger.error(f"Error converting bytes to image: {e}")
            return None
    
    def _run_yolo_detection(self, image: np.ndarray, image_index: int = 0) -> List[Dict[str, Any]]:
        """Run YOLO detection on image"""
        try:
            # Get image dimensions
            height, width = image.shape[:2]
            
            # Run YOLO inference
            results = self.model(image, verbose=False)
            
            detections = []
            
            # Process results
            for result in results:
                boxes = result.boxes
                if boxes is not None:
                    for i, box in enumerate(boxes):
                        # Extract bounding box coordinates
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        
                        # Get confidence and class
                        confidence = float(box.conf[0].cpu().numpy())
                        class_id = int(box.cls[0].cpu().numpy())
                        # Use model's built-in class names
                        class_name = self.model.names[class_id]
                        
                        # Calculate additional location information
                        location_info = self._calculate_location_info(
                            x1, y1, x2, y2, width, height
                        )
                        
                        detection = {
                            "object_id": len(detections) + 1,
                            "image_index": image_index,
                            "name": class_name,
                            "class_id": class_id,
                            "confidence": confidence,
                            "location": location_info,
                            "detection_timestamp": datetime.now().isoformat()
                        }
                        
                        detections.append(detection)
            
            # Sort by confidence (highest first)
            detections.sort(key=lambda x: x["confidence"], reverse=True)
            
            return detections
            
        except Exception as e:
            logger.error(f"Error in YOLO detection: {e}")
            return []
    
    def _calculate_location_info(self, x1: float, y1: float, x2: float, y2: float, 
                                image_width: int, image_height: int) -> Dict[str, Any]:
        """Calculate comprehensive location information"""
        
        # Convert to integers
        x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
        
        # Calculate center point
        center_x = (x1 + x2) // 2
        center_y = (y1 + y2) // 2
        
        # Calculate dimensions
        width = x2 - x1
        height = y2 - y1
        area = width * height
        
        # Calculate area percentage
        total_image_area = image_width * image_height
        area_percentage = (area / total_image_area) * 100
        
        # Calculate relative position
        relative_position = self._get_relative_position(center_x, center_y, image_width, image_height)
        
        # Calculate normalized coordinates (0-1 range)
        normalized_coords = {
            "x1": x1 / image_width,
            "y1": y1 / image_height,
            "x2": x2 / image_width,
            "y2": y2 / image_height,
            "center_x": center_x / image_width,
            "center_y": center_y / image_height
        }
        
        return {
            "bounding_box": {
                "x1": x1, "y1": y1, "x2": x2, "y2": y2
            },
            "center": {
                "x": center_x, "y": center_y
            },
            "dimensions": {
                "width": width, "height": height, "area": area
            },
            "relative_position": relative_position,
            "area_percentage": round(area_percentage, 2),
            "normalized_coordinates": normalized_coords
        }
    
    def _get_relative_position(self, center_x: int, center_y: int, 
                              image_width: int, image_height: int) -> str:
        """Get human-readable relative position"""
        
        # Determine horizontal position
        if center_x < image_width / 3:
            horizontal = "left"
        elif center_x < 2 * image_width / 3:
            horizontal = "center"
        else:
            horizontal = "right"
        
        # Determine vertical position
        if center_y < image_height / 3:
            vertical = "top"
        elif center_y < 2 * image_height / 3:
            vertical = "middle"
        else:
            vertical = "bottom"
        
        # Combine positions
        if horizontal == "center" and vertical == "middle":
            return "center"
        elif horizontal == "center":
            return f"{vertical}-center"
        elif vertical == "middle":
            return f"{horizontal}-center"
        else:
            return f"{vertical}-{horizontal}"
    
    def _save_detections_to_json(self, detections: List[Dict[str, Any]], 
                                metadata: Dict[str, Any]) -> str:
        """Save detection results to JSON file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"yolo_detections_{timestamp}.json"
            filepath = os.path.join(self.output_dir, filename)
            
            # Create comprehensive JSON structure
            json_data = {
                "detection_metadata": metadata,
                "detections": detections,
                "summary": {
                    "unique_classes": list(set([d["name"] for d in detections])),
                    "class_counts": self._get_class_counts(detections),
                    "confidence_stats": self._get_confidence_stats(detections)
                }
            }
            
            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Detection results saved to {filepath}")
            return filename
            
        except Exception as e:
            logger.error(f"Error saving JSON: {e}")
            return "error_saving_json"
    
    def _get_class_counts(self, detections: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get count of each detected class"""
        class_counts = {}
        for detection in detections:
            class_name = detection["name"]
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        return class_counts
    
    def _get_confidence_stats(self, detections: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate confidence statistics"""
        if not detections:
            return {"min": 0, "max": 0, "average": 0}
        
        confidences = [d["confidence"] for d in detections]
        return {
            "min": round(min(confidences), 3),
            "max": round(max(confidences), 3),
            "average": round(sum(confidences) / len(confidences), 3)
        }
    
    def _format_detection_response(self, detections: List[Dict[str, Any]], 
                                  metadata: Dict[str, Any], json_filename: str) -> str:
        """Format detection results for user response"""
        
        response = "🔍 **YOLO Detection Complete!**\n\n"
        response += f"📊 **Summary:**\n"
        response += f"• Objects detected: {metadata['total_objects']}\n"
        response += f"• Processing time: {metadata['processing_time']}\n"
        response += f"• Images processed: {metadata['image_count']}\n\n"
        
        if detections:
            response += "🎯 **Detected Objects:**\n\n"
            
            for i, detection in enumerate(detections[:10], 1):  # Show top 10
                name = detection["name"].replace("_", " ").title()
                confidence = detection["confidence"]
                position = detection["location"]["relative_position"]
                area_pct = detection["location"]["area_percentage"]
                
                response += f"{i}. **{name}**\n"
                response += f"   🎯 Confidence: {confidence:.1%}\n"
                response += f"   📍 Position: {position}\n"
                response += f"   📏 Area: {area_pct}% of image\n\n"
            
            if len(detections) > 10:
                response += f"... and {len(detections) - 10} more objects\n\n"
        
        response += f"💾 **Results saved to:** `{json_filename}`\n"
        response += f"📂 **Location:** `yolo_outputs/` directory\n\n"
        response += "Let me check our inventory for any matching products..."
        
        return response
    
    def _format_no_detection_response(self) -> str:
        """Format response when no objects are detected"""
        
        return """❌ No objects detected in your image!"""
    
    def _validate_image(self, image_data: bytes) -> bool:
        """Validate image data"""
        try:
            image = Image.open(io.BytesIO(image_data))
            
            # Check image format
            if image.format not in ['JPEG', 'PNG', 'JPG', 'WEBP']:
                logger.warning(f"Unsupported image format: {image.format}")
                return False
            
            # Check image size
            width, height = image.size
            if width < 32 or height < 32:
                logger.warning(f"Image too small: {width}x{height}")
                return False
            
            if width > 4096 or height > 4096:
                logger.warning(f"Image too large: {width}x{height}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Image validation error: {e}")
            return False
    
    def get_supported_classes(self) -> List[str]:
        """Get list of supported classes from the loaded model"""
        if self.model and hasattr(self.model, 'names'):
            return list(self.model.names.values())
        return []
    
    def get_detection_file(self, filename: str) -> Optional[Dict[str, Any]]:
        """Load detection results from JSON file"""
        try:
            filepath = os.path.join(self.output_dir, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading detection file: {e}")
            return None