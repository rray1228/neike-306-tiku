import AppKit
import Foundation
import Vision

guard CommandLine.arguments.count == 3 else {
    fputs("usage: ocr_pages_vision <input-directory> <output-jsonl>\n", stderr)
    exit(2)
}

let inputDirectory = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
let outputURL = URL(fileURLWithPath: CommandLine.arguments[2])
let fileManager = FileManager.default

let imageURLs = try fileManager.contentsOfDirectory(
    at: inputDirectory,
    includingPropertiesForKeys: nil,
    options: [.skipsHiddenFiles]
).filter { $0.pathExtension.lowercased() == "png" }
 .sorted { $0.lastPathComponent.localizedStandardCompare($1.lastPathComponent) == .orderedAscending }

fileManager.createFile(atPath: outputURL.path, contents: nil)
let output = try FileHandle(forWritingTo: outputURL)
defer { try? output.close() }

for (index, imageURL) in imageURLs.enumerated() {
    guard
        let image = NSImage(contentsOf: imageURL),
        let tiff = image.tiffRepresentation,
        let bitmap = NSBitmapImageRep(data: tiff),
        let cgImage = bitmap.cgImage
    else {
        fputs("cannot read \(imageURL.path)\n", stderr)
        continue
    }

    let width = CGFloat(cgImage.width)
    let height = CGFloat(cgImage.height)
    let request = VNRecognizeTextRequest()
    request.recognitionLevel = .accurate
    request.recognitionLanguages = ["zh-Hans", "en-US"]
    request.usesLanguageCorrection = true
    request.minimumTextHeight = 0.008

    let handler = VNImageRequestHandler(cgImage: cgImage, options: [:])
    try handler.perform([request])

    let rows: [[String: Any]] = (request.results ?? []).compactMap { observation in
        guard let candidate = observation.topCandidates(1).first else { return nil }
        let box = observation.boundingBox
        let x0 = box.minX * width
        let x1 = box.maxX * width
        let y0 = (1 - box.maxY) * height
        let y1 = (1 - box.minY) * height
        return [
            "text": candidate.string,
            "score": candidate.confidence,
            "box": [
                [x0, y0],
                [x1, y0],
                [x1, y1],
                [x0, y1],
            ],
        ]
    }.sorted {
        let lhs = ($0["box"] as! [[CGFloat]])[0]
        let rhs = ($1["box"] as! [[CGFloat]])[0]
        if abs(lhs[1] - rhs[1]) > 6 { return lhs[1] < rhs[1] }
        return lhs[0] < rhs[0]
    }

    let pageNumber = Int(
        imageURL.deletingPathExtension().lastPathComponent
            .split(separator: "-").last ?? ""
    ) ?? (index + 1)
    let record: [String: Any] = [
        "page": pageNumber,
        "width": cgImage.width,
        "height": cgImage.height,
        "rows": rows,
    ]
    let data = try JSONSerialization.data(withJSONObject: record)
    output.write(data)
    output.write(Data([0x0A]))
    fputs("ocr \(index + 1)/\(imageURLs.count): \(imageURL.lastPathComponent)\n", stderr)
}
