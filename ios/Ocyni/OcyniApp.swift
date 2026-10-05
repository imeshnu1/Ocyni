import SwiftUI

@main
struct OcyniApp: App {
    @AppStorage("seafarerName") private var seafarerName: String = ""

    var body: some Scene {
        WindowGroup {
            Group {
                if seafarerName.trimmingCharacters(in: .whitespaces).isEmpty {
                    OnboardingView()
                } else {
                    HomeView()
                }
            }
            .preferredColorScheme(.dark)
        }
    }
}
