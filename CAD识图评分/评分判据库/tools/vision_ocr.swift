import Foundation
import Vision
import AppKit
// 本地读取，不上传。输出坐标为像素、左上角原点。
for filename in CommandLine.arguments.dropFirst() {
    do {
        let url = URL(fileURLWithPath: filename)
        guard let im = NSImage(contentsOf: url), let cg = im.cgImage(forProposedRect: nil, context: nil, hints: nil) else { throw NSError(domain:"image",code:1) }
        let req = VNRecognizeTextRequest()
        req.recognitionLevel = .accurate
        req.recognitionLanguages = ["zh-Hans", "en-US"]
        req.usesLanguageCorrection = false
        try VNImageRequestHandler(cgImage: cg, options: [:]).perform([req])
        let records: [[String:Any]] = (req.results ?? []).compactMap { ob in
            guard let candidate = ob.topCandidates(1).first else { return nil }
            let b=ob.boundingBox; let w=Double(cg.width);let h=Double(cg.height)
            return ["text":candidate.string,"confidence":Double(candidate.confidence),"bbox":[b.minX*w,(1-b.maxY)*h,b.maxX*w,(1-b.minY)*h]]
        }
        let obj:[String:Any] = ["file": filename,"status":records.isEmpty ? "EMPTY" : "OK","width":cg.width,"height":cg.height,"engine":"Apple Vision","revision":req.revision,"records":records]
        let data = try JSONSerialization.data(withJSONObject:obj,options:[.sortedKeys])
        print(String(data:data,encoding:.utf8)!)
    } catch {
        let obj:[String:Any] = ["file":filename,"status":"ERROR","reason":String(describing:error)]
        let data=try! JSONSerialization.data(withJSONObject:obj); print(String(data:data,encoding:.utf8)!)
    }
}
