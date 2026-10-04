// VIA lib.itext 接頭:`java -jar itext-cli.jar <pdf>` → stdout 逐頁文字(AGPL 授權註記;唯讀)。
// 契約:成功 rc 0;任何錯誤印 stderr、rc 1。只用本機免費核心,不接付費雲服務。
import com.itextpdf.kernel.pdf.PdfDocument;
import com.itextpdf.kernel.pdf.PdfReader;
import com.itextpdf.kernel.pdf.canvas.parser.PdfTextExtractor;

public final class ExtractText {
    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("usage: java -jar itext-cli.jar <pdf>");
            System.exit(1);
        }
        try (PdfDocument doc = new PdfDocument(new PdfReader(args[0]))) {
            int n = doc.getNumberOfPages();
            for (int i = 1; i <= n; i++) {
                System.out.println(PdfTextExtractor.getTextFromPage(doc.getPage(i)));
            }
        } catch (Exception e) {
            System.err.println("itext extract error: " + e);
            System.exit(1);
        }
    }
}
