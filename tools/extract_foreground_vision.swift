import AppKit
import CoreImage
import Foundation
import Vision

guard CommandLine.arguments.count == 3 else {
    FileHandle.standardError.write(Data("usage: extract_foreground_vision.swift input.png output.png\n".utf8))
    exit(2)
}

let sourceURL = URL(fileURLWithPath: CommandLine.arguments[1])
let outputURL = URL(fileURLWithPath: CommandLine.arguments[2])

guard let source = CIImage(contentsOf: sourceURL) else {
    throw NSError(domain: "ForegroundExtract", code: 1, userInfo: [NSLocalizedDescriptionKey: "Cannot read input image"])
}

let request = VNGeneratePersonSegmentationRequest()
request.qualityLevel = .accurate
request.outputPixelFormat = kCVPixelFormatType_OneComponent8
let handler = VNImageRequestHandler(ciImage: source, options: [:])
try handler.perform([request])

guard let observation = request.results?.first else {
    throw NSError(domain: "ForegroundExtract", code: 2, userInfo: [NSLocalizedDescriptionKey: "No person mask found"])
}

CVPixelBufferLockBaseAddress(observation.pixelBuffer, .readOnly)
if let base = CVPixelBufferGetBaseAddress(observation.pixelBuffer) {
    let width = CVPixelBufferGetWidth(observation.pixelBuffer)
    let height = CVPixelBufferGetHeight(observation.pixelBuffer)
    let stride = CVPixelBufferGetBytesPerRow(observation.pixelBuffer)
    let bytes = base.assumingMemoryBound(to: UInt8.self)
    var minimum = UInt8.max
    var maximum = UInt8.min
    for y in 0..<height {
        for x in 0..<width {
            let value = bytes[y * stride + x]
            minimum = min(minimum, value)
            maximum = max(maximum, value)
        }
    }
    print("person mask \(width)x\(height) range \(minimum)...\(maximum)")
}
CVPixelBufferUnlockBaseAddress(observation.pixelBuffer, .readOnly)

let rawMask = CIImage(cvPixelBuffer: observation.pixelBuffer)
let mask = rawMask.transformed(
    by: CGAffineTransform(
        scaleX: source.extent.width / rawMask.extent.width,
        y: source.extent.height / rawMask.extent.height
    )
)
let alphaMask = mask.applyingFilter("CIMaskToAlpha")
guard let composite = CIFilter(name: "CISourceInCompositing") else {
    throw NSError(domain: "ForegroundExtract", code: 3, userInfo: [NSLocalizedDescriptionKey: "Cannot create source-in filter"])
}
composite.setValue(source, forKey: kCIInputImageKey)
composite.setValue(alphaMask, forKey: kCIInputBackgroundImageKey)

guard let output = composite.outputImage?.cropped(to: source.extent) else {
    throw NSError(domain: "ForegroundExtract", code: 4, userInfo: [NSLocalizedDescriptionKey: "Cannot produce output image"])
}

let context = CIContext(options: [.useSoftwareRenderer: false])
try context.writePNGRepresentation(
    of: output,
    to: outputURL,
    format: .RGBA8,
    colorSpace: CGColorSpaceCreateDeviceRGB()
)
