import SwiftUI

struct OnboardingView: View {
    @AppStorage("seafarerName") private var seafarerName: String = ""
    @State private var name: String = ""
    @FocusState private var focused: Bool

    var body: some View {
        ZStack {
            CalmBackground()
            VStack(spacing: 28) {
                Spacer()
                Text("Welcome aboard.")
                    .font(.largeTitle)
                    .fontWeight(.semibold)
                    .foregroundStyle(.white.opacity(0.95))
                Text("Ocyni is a quiet place to check in with yourself at sea.\nWhat should I call you?")
                    .font(.body)
                    .foregroundStyle(.white.opacity(0.7))
                    .multilineTextAlignment(.center)
                    .lineSpacing(4)
                TextField("Your name", text: $name)
                    .textFieldStyle(.roundedBorder)
                    .font(.title3)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 48)
                    .focused($focused)
                    .submitLabel(.done)
                    .onSubmit(continueTapped)
                Button(action: continueTapped) {
                    Text("Continue")
                        .font(.headline)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 14)
                }
                .buttonStyle(.borderedProminent)
                .tint(.teal.opacity(0.7))
                .padding(.horizontal, 48)
                .disabled(name.trimmingCharacters(in: .whitespaces).isEmpty)
                Spacer()
                DisclaimerFooter()
            }
            .padding()
        }
        .onAppear { focused = true }
    }

    private func continueTapped() {
        let trimmed = name.trimmingCharacters(in: .whitespaces)
        guard !trimmed.isEmpty else { return }
        seafarerName = trimmed
    }
}
