import SwiftUI

struct CopingView: View {
    let preselectedExerciseId: String?

    @State private var exercises: [ExerciseSummary] = []
    @State private var isLoading = true
    @State private var errorText: String? = nil
    @State private var selected: ExerciseDetail? = nil

    init(preselectedExerciseId: String? = nil) {
        self.preselectedExerciseId = preselectedExerciseId
    }

    var body: some View {
        ZStack {
            CalmBackground()
            Group {
                if isLoading {
                    ProgressView().tint(.white)
                } else {
                    List(exercises) { ex in
                        Button { Task { await openDetail(id: ex.id) } } label: {
                            HStack {
                                VStack(alignment: .leading, spacing: 4) {
                                    Text(ex.title)
                                        .font(.headline)
                                        .foregroundStyle(.white)
                                    Text("\(ex.category.capitalized) · \(ex.durationMinutes) min")
                                        .font(.subheadline)
                                        .foregroundStyle(.white.opacity(0.6))
                                }
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .foregroundStyle(.white.opacity(0.4))
                            }
                            .padding(.vertical, 6)
                        }
                        .listRowBackground(Color.clear)
                        .listRowSeparator(.hidden)
                    }
                    .listStyle(.plain)
                    .scrollContentBackground(.hidden)
                }
            }
        }
        .navigationTitle("Coping exercises")
        .sheet(item: $selected) { detail in
            ExerciseSessionView(exercise: detail)
        }
        .task {
            await load()
            if let id = preselectedExerciseId {
                await openDetail(id: id)
            }
        }
        .alert("Couldn't load", isPresented: .constant(errorText != nil)) {
            Button("OK") { errorText = nil }
        } message: {
            Text(errorText ?? "")
        }
    }

    private func load() async {
        do {
            let list = try await APIClient.shared.listExercises()
            await MainActor.run {
                exercises = list
                isLoading = false
            }
        } catch {
            await MainActor.run {
                errorText = error.localizedDescription
                isLoading = false
            }
        }
    }

    private func openDetail(id: String) async {
        do {
            let detail = try await APIClient.shared.exerciseDetail(id: id)
            await MainActor.run { selected = detail }
        } catch {
            await MainActor.run { errorText = error.localizedDescription }
        }
    }
}

private struct ExerciseSessionView: View {
    let exercise: ExerciseDetail
    @Environment(\.dismiss) private var dismiss

    @State private var mood: Int? = nil
    @State private var onWatch = false
    @State private var isStarting = false
    @State private var deferredMessage: String? = nil
    @State private var session: CopingSessionOut? = nil
    @State private var moodAfter: Int? = nil
    @State private var isCompleting = false
    @State private var errorText: String? = nil

    var body: some View {
        NavigationStack {
            ZStack {
                CalmBackground()
                ScrollView {
                    VStack(alignment: .leading, spacing: 20) {
                        Text(exercise.title)
                            .font(.largeTitle)
                            .fontWeight(.semibold)
                            .foregroundStyle(.white.opacity(0.95))
                        Text("\(exercise.durationMinutes) minutes · \(exercise.category.capitalized)")
                            .font(.subheadline)
                            .foregroundStyle(.white.opacity(0.6))
                        Text(exercise.maritimeNote)
                            .font(.body)
                            .italic()
                            .foregroundStyle(.teal.opacity(0.9))

                        VStack(alignment: .leading, spacing: 12) {
                            ForEach(Array(exercise.steps.enumerated()), id: \.offset) { i, step in
                                VStack(alignment: .leading, spacing: 4) {
                                    Text("Step \(i + 1) — \(step.title)")
                                        .font(.headline)
                                        .foregroundStyle(.white.opacity(0.9))
                                    Text(step.instruction)
                                        .font(.body)
                                        .foregroundStyle(.white.opacity(0.75))
                                        .lineSpacing(2)
                                }
                            }
                        }

                        if let session {
                            // Session in progress / done
                            SoftCard {
                                VStack(alignment: .leading, spacing: 10) {
                                    Text("How do you feel now?")
                                        .font(.headline)
                                        .foregroundStyle(.white)
                                    MoodDots(mood: $moodAfter)
                                    Button {
                                        complete()
                                    } label: {
                                        HStack {
                                            if isCompleting { ProgressView().tint(.white) }
                                            Text("Done — complete session")
                                        }
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 12)
                                    }
                                    .buttonStyle(.borderedProminent)
                                    .tint(.teal.opacity(0.65))
                                    .disabled(moodAfter == nil || isCompleting || session.completed)
                                    if let shift = session.moodShift {
                                        Text(shiftMessage(shift))
                                            .font(.body)
                                            .foregroundStyle(.white.opacity(0.9))
                                    }
                                }
                            }
                            if session.crisisFlag, let support = session.support {
                                CrisisSupportCard(support: support)
                            }
                        } else {
                            // Pre-session
                            SoftCard {
                                VStack(alignment: .leading, spacing: 12) {
                                    Text("Before we begin")
                                        .font(.headline)
                                        .foregroundStyle(.white)
                                    Text("How do you feel right now?")
                                        .font(.subheadline)
                                        .foregroundStyle(.white.opacity(0.7))
                                    MoodDots(mood: $mood)
                                    Toggle("I'm on watch right now", isOn: $onWatch)
                                        .foregroundStyle(.white.opacity(0.85))
                                    if let errorText {
                                        Text(errorText)
                                            .font(.subheadline)
                                            .foregroundStyle(.orange)
                                    }
                                    if let deferredMessage {
                                        Text(deferredMessage)
                                            .font(.body)
                                            .foregroundStyle(.white.opacity(0.9))
                                            .lineSpacing(3)
                                    }
                                    Button {
                                        start()
                                    } label: {
                                        HStack {
                                            if isStarting { ProgressView().tint(.white) }
                                            Text("Start guided session")
                                        }
                                        .frame(maxWidth: .infinity)
                                        .padding(.vertical, 12)
                                    }
                                    .buttonStyle(.borderedProminent)
                                    .tint(.teal.opacity(0.65))
                                    .disabled(mood == nil || isStarting)
                                }
                            }
                        }

                        DisclaimerFooter()
                    }
                    .padding()
                }
            }
            .navigationTitle(exercise.title)
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Close") { dismiss() }
                }
            }
        }
    }

    private func shiftMessage(_ shift: Int) -> String {
        if shift > 0 { return "Your mood lifted by \(shift) — nice. Hold onto that." }
        if shift < 0 { return "Tough one — no shame in that. Be gentle with yourself tonight." }
        return "Steady. Sometimes holding the line is the win."
    }

    private func start() {
        guard let mood else { return }
        isStarting = true
        errorText = nil
        deferredMessage = nil
        Task {
            do {
                let result = try await APIClient.shared.startSession(
                    exerciseId: exercise.id, mood: mood, onWatch: onWatch, note: nil
                )
                await MainActor.run {
                    switch result {
                    case .started(let s): session = s
                    case .deferred(let msg): deferredMessage = msg
                    }
                    isStarting = false
                }
            } catch {
                await MainActor.run {
                    errorText = error.localizedDescription
                    isStarting = false
                }
            }
        }
    }

    private func complete() {
        guard let session, let moodAfter else { return }
        isCompleting = true
        Task {
            do {
                let done = try await APIClient.shared.completeSession(id: session.id, moodAfter: moodAfter)
                await MainActor.run {
                    self.session = done
                    isCompleting = false
                }
            } catch {
                await MainActor.run {
                    errorText = error.localizedDescription
                    isCompleting = false
                }
            }
        }
    }
}
