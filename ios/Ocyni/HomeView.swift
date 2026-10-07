import SwiftUI

// MARK: - Shared calm UI

struct CalmBackground: View {
    var body: some View {
        LinearGradient(
            colors: [
                Color(red: 0.04, green: 0.10, blue: 0.16),
                Color(red: 0.07, green: 0.16, blue: 0.22),
                Color(red: 0.05, green: 0.12, blue: 0.18),
            ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()
    }
}

struct SoftCard<Content: View>: View {
    let content: Content
    init(@ViewBuilder content: () -> Content) { self.content = content() }

    var body: some View {
        content
            .padding(18)
            .background(.white.opacity(0.07))
            .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
            .overlay(
                RoundedRectangle(cornerRadius: 18, style: .continuous)
                    .stroke(.white.opacity(0.08), lineWidth: 1)
            )
    }
}

struct MoodDots: View {
    @Binding var mood: Int?

    var body: some View {
        HStack(spacing: 14) {
            ForEach(1...5, id: \.self) { value in
                Button {
                    mood = (mood == value) ? nil : value
                } label: {
                    Circle()
                        .fill(mood == value ? Color.teal.opacity(0.85) : .white.opacity(0.14))
                        .frame(width: 40, height: 40)
                        .overlay(
                            Text("\(value)")
                                .font(.headline)
                                .foregroundStyle(mood == value ? .black : .white.opacity(0.8))
                        )
                }
                .accessibilityLabel("Mood \(value) of 5")
            }
        }
    }
}

struct CrisisSupportCard: View {
    let support: SupportPayload

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(support.message)
                .font(.body)
                .foregroundStyle(.white.opacity(0.95))
            ForEach(support.resources, id: \.name) { r in
                VStack(alignment: .leading, spacing: 2) {
                    Text(r.name).font(.headline).foregroundStyle(.white)
                    Text(r.contact).font(.subheadline).foregroundStyle(.white.opacity(0.75))
                }
                .padding(.vertical, 4)
            }
        }
        .padding(18)
        .background(Color.red.opacity(0.16))
        .clipShape(RoundedRectangle(cornerRadius: 18, style: .continuous))
        .overlay(
            RoundedRectangle(cornerRadius: 18, style: .continuous)
                .stroke(.red.opacity(0.4), lineWidth: 1)
        )
    }
}

struct DisclaimerFooter: View {
    var body: some View {
        Text("Ocyni is a wellness tool, not medical advice.\nIf you're struggling, please reach out — 988 (US) or seafarerhelp.org.")
            .font(.caption2)
            .foregroundStyle(.white.opacity(0.4))
            .multilineTextAlignment(.center)
            .lineSpacing(2)
    }
}

// MARK: - Home

private enum HomeDestination: Hashable {
    case journal
    case sleep
    case coping(exerciseId: String?)
}

struct HomeView: View {
    @AppStorage("seafarerName") private var name: String = ""
    @State private var message: String = ""
    @State private var mood: Int? = nil
    @State private var isWorking = false
    @State private var result: RecommendResponse? = nil
    @State private var errorText: String? = nil
    @State private var path: [HomeDestination] = []
    @FocusState private var messageFocused: Bool

    private var greeting: String {
        let hour = Calendar.current.component(.hour, from: Date())
        let first = name.split(separator: " ").first.map(String.init) ?? name
        switch hour {
        case 5..<12: return "Good morning, \(first),"
        case 12..<17: return "Good afternoon, \(first),"
        case 17..<23: return "Good evening, \(first),"
        default: return "Up late, \(first)?"
        }
    }

    private var canTalk: Bool {
        !message.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty || mood != nil
    }

    var body: some View {
        NavigationStack(path: $path) {
            ZStack {
                CalmBackground()
                ScrollView {
                    VStack(alignment: .leading, spacing: 24) {
                        Text(greeting)
                            .font(.largeTitle)
                            .fontWeight(.semibold)
                            .foregroundStyle(.white.opacity(0.95))
                            .padding(.top, 24)

                        Text("How has your day been?")
                            .font(.title3)
                            .foregroundStyle(.white.opacity(0.75))

                        TextField("A few words, if you like…", text: $message, axis: .vertical)
                            .lineLimit(2...6)
                            .padding(14)
                            .background(.white.opacity(0.08))
                            .clipShape(RoundedRectangle(cornerRadius: 14, style: .continuous))
                            .foregroundStyle(.white)
                            .focused($messageFocused)

                        MoodDots(mood: $mood)

                        Button(action: talk) {
                            HStack {
                                if isWorking { ProgressView().tint(.white) }
                                Text(isWorking ? "Listening…" : "Talk")
                                    .font(.headline)
                            }
                            .frame(maxWidth: .infinity)
                            .padding(.vertical, 14)
                        }
                        .buttonStyle(.borderedProminent)
                        .tint(.teal.opacity(0.65))
                        .disabled(!canTalk || isWorking)

                        if let errorText {
                            Text(errorText)
                                .font(.subheadline)
                                .foregroundStyle(.orange.opacity(0.9))
                        }

                        if let recommendation = result {
                            SoftCard {
                                VStack(alignment: .leading, spacing: 10) {
                                    Text(recommendation.reply)
                                        .font(.body)
                                        .foregroundStyle(.white.opacity(0.92))
                                        .lineSpacing(3)
                                }
                            }

                            if recommendation.crisisFlag, let support = recommendation.support {
                                CrisisSupportCard(support: support)
                            } else if recommendation.recommendation.feature != "none" {
                                SoftCard {
                                    VStack(alignment: .leading, spacing: 8) {
                                        Text(recommendation.recommendation.title)
                                            .font(.headline)
                                            .foregroundStyle(.white)
                                        Text(recommendation.recommendation.reason)
                                            .font(.subheadline)
                                            .foregroundStyle(.white.opacity(0.7))
                                        Button("Open") { openRecommendation(recommendation.recommendation) }
                                            .buttonStyle(.bordered)
                                            .tint(.teal)
                                    }
                                }
                            }

                            Button("Start over") {
                                result = nil
                                errorText = nil
                                message = ""
                                mood = nil
                            }
                            .font(.subheadline)
                            .foregroundStyle(.white.opacity(0.6))
                        }

                        Spacer(minLength: 12)
                        DisclaimerFooter()
                    }
                    .padding(.horizontal, 22)
                    .padding(.bottom, 24)
                }
                .scrollDismissesKeyboard(.interactively)
            }
            .navigationDestination(for: HomeDestination.self) { dest in
                switch dest {
                case .journal: JournalView()
                case .sleep: SleepView()
                case .coping(let id): CopingView(preselectedExerciseId: id)
                }
            }
        }
    }

    private func talk() {
        messageFocused = false
        errorText = nil
        isWorking = true
        let text = message.trimmingCharacters(in: .whitespacesAndNewlines)
        let tappedMood = mood
        Task {
            do {
                let response = try await APIClient.shared.recommend(
                    message: text.isEmpty ? nil : text,
                    mood: tappedMood,
                    name: name
                )
                // Quietly log the mood tap alongside the check-in.
                if let tappedMood {
                    _ = try? await APIClient.shared.moodCheckin(score: tappedMood)
                }
                await MainActor.run {
                    result = response
                    isWorking = false
                }
            } catch {
                await MainActor.run {
                    errorText = error.localizedDescription
                    isWorking = false
                }
            }
        }
    }

    private func openRecommendation(_ rec: Recommendation) {
        switch rec.feature {
        case "journal": path.append(.journal)
        case "sleep": path.append(.sleep)
        case "coping": path.append(.coping(exerciseId: rec.exerciseId))
        default: break
        }
    }
}
